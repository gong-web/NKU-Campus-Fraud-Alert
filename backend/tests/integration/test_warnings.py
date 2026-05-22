"""集成：预警发布与管理（UC-03 / UC-07）。

覆盖：
- 全校紧急预警发布 → 学生可见
- 按院系推送 → 命中学生可见 / 未命中院系学生不可见
- 院级 reviewer 发紧急预警 → 403 PermissionDenied
- 已下线预警追加 → 409；连续 offline → 409
- 学生越权调用 admin POST → 403
- 入参校验：DEPARTMENT 不传 target_dept_ids → 422
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.infra.cache.rbac_cache import RBACCache
from app.infra.db.models import (
    Department,
    Permission,
    Role,
    RolePermission,
    User,
)
from app.infra.db.models.user import UserStatus
from app.infra.repositories.role import RoleRepository
from app.services import permissions as perm

pytestmark = pytest.mark.integration


# ── 测试 seed ────────────────────────────────────────────────────────


@pytest.fixture
async def seed_warnings_minimum(db_session):
    """最小 seed：3 个院系 + 4 个角色 + 权限矩阵 + 4 个用户。

    用户：
      - student001 (CS, STUDENT)
      - student002 (MATH, STUDENT)
      - reviewer_dept001 (CS, REVIEWER level=1)
      - reviewer_school001 (UNKNOWN, REVIEWER level=2)
    """
    # 1. 院系
    dept_unknown = Department(dept_code="UNKNOWN", dept_name="未指定", dept_level=1, sort_order=0)
    dept_cs = Department(dept_code="CS", dept_name="计算机学院", dept_level=1, sort_order=1)
    dept_math = Department(dept_code="MATH", dept_name="数学学院", dept_level=1, sort_order=2)
    db_session.add_all([dept_unknown, dept_cs, dept_math])
    await db_session.flush()

    # 2. 角色：STUDENT(level=1), REVIEWER(level=1), REVIEWER(level=2)
    student_role = Role(role_code=Role.CODE_STUDENT, role_name="学生", role_level=1)
    reviewer_dept_role = Role(role_code=Role.CODE_REVIEWER, role_name="院级审核员", role_level=1)
    reviewer_school_role = Role(role_code=Role.CODE_REVIEWER, role_name="校级审核员", role_level=2)
    db_session.add_all([student_role, reviewer_dept_role, reviewer_school_role])
    await db_session.flush()

    # 3. 权限
    p_read = Permission(
        permission_code=perm.WARNING_READ,
        permission_name="查看预警",
        resource_type="WARNING",
        action_type="READ",
    )
    p_publish = Permission(
        permission_code=perm.WARNING_PUBLISH,
        permission_name="发布预警",
        resource_type="WARNING",
        action_type="PUBLISH",
    )
    p_append = Permission(
        permission_code=perm.WARNING_APPEND,
        permission_name="追加预警",
        resource_type="WARNING",
        action_type="APPEND",
    )
    p_offline = Permission(
        permission_code=perm.WARNING_OFFLINE,
        permission_name="下线预警",
        resource_type="WARNING",
        action_type="OFFLINE",
    )
    db_session.add_all([p_read, p_publish, p_append, p_offline])
    await db_session.flush()

    # 4. 角色权限矩阵
    db_session.add_all(
        [
            # STUDENT 只能读
            RolePermission(role_id=student_role.role_id, permission_id=p_read.permission_id),
            # 院级 reviewer：发布 + 追加 + 下线（紧急级在 service 层再校验）
            RolePermission(role_id=reviewer_dept_role.role_id, permission_id=p_read.permission_id),
            RolePermission(role_id=reviewer_dept_role.role_id, permission_id=p_publish.permission_id),
            RolePermission(role_id=reviewer_dept_role.role_id, permission_id=p_append.permission_id),
            RolePermission(role_id=reviewer_dept_role.role_id, permission_id=p_offline.permission_id),
            # 校级 reviewer：全权限
            RolePermission(role_id=reviewer_school_role.role_id, permission_id=p_read.permission_id),
            RolePermission(role_id=reviewer_school_role.role_id, permission_id=p_publish.permission_id),
            RolePermission(role_id=reviewer_school_role.role_id, permission_id=p_append.permission_id),
            RolePermission(role_id=reviewer_school_role.role_id, permission_id=p_offline.permission_id),
        ]
    )
    await db_session.flush()

    # 5. 用户
    users = [
        User(
            user_id=8101,
            cas_account="student001",
            real_name="学生甲(CS)",
            department_id=dept_cs.dept_id,
            role_id=student_role.role_id,
            status=UserStatus.ACTIVE.value,
        ),
        User(
            user_id=8102,
            cas_account="student002",
            real_name="学生乙(MATH)",
            department_id=dept_math.dept_id,
            role_id=student_role.role_id,
            status=UserStatus.ACTIVE.value,
        ),
        User(
            user_id=8201,
            cas_account="reviewer_dept001",
            real_name="院级审核员",
            department_id=dept_cs.dept_id,
            role_id=reviewer_dept_role.role_id,
            status=UserStatus.ACTIVE.value,
        ),
        User(
            user_id=8202,
            cas_account="reviewer_school001",
            real_name="校级审核员",
            department_id=dept_unknown.dept_id,
            role_id=reviewer_school_role.role_id,
            status=UserStatus.ACTIVE.value,
        ),
    ]
    db_session.add_all(users)
    await db_session.commit()

    # 6. 预热 RBAC 缓存
    async with __import__("app.infra.db.session", fromlist=["uow"]).uow() as session:
        mapping = await RoleRepository(session).list_role_permissions_full()
    await RBACCache().load(mapping)

    return {
        "dept_unknown_id": dept_unknown.dept_id,
        "dept_cs_id": dept_cs.dept_id,
        "dept_math_id": dept_math.dept_id,
        "student_role_id": student_role.role_id,
        "reviewer_dept_role_id": reviewer_dept_role.role_id,
        "reviewer_school_role_id": reviewer_school_role.role_id,
    }


async def _login(client: AsyncClient, cas_account: str) -> None:
    r = await client.post(
        "/api/v1/auth/cas/mock-login",
        json={"cas_account": cas_account},
    )
    assert r.status_code == 200, r.text


# ── 发布 / 推送 / 学生可见性 ────────────────────────────────────────


@pytest.mark.asyncio
async def test_publish_warning_full_school_ok(
    client: AsyncClient, seed_warnings_minimum
) -> None:
    """reviewer_school 发 FULL_SCHOOL 紧急预警 → 201；学生1能看到，列表中也能命中。"""
    await _login(client, "reviewer_school001")

    r = await client.post(
        "/api/v1/admin/warnings",
        json={
            "title": "紧急·冒充客服退款电话激增",
            "content": "近日多名同学接到冒充客服来电要求退款，请同学们提高警惕、不点击不明链接。",
            "warning_level": 3,
            "push_scope": "FULL_SCHOOL",
        },
    )
    assert r.status_code == 201, r.text
    warning = r.json()
    warning_id = warning["warning_id"]
    assert warning["status"] == "ONLINE"
    assert warning["push_scope"] == "FULL_SCHOOL"
    assert warning["warning_level"] == 3

    # 学生 1 登录看详情
    await _login(client, "student001")
    detail = await client.get(f"/api/v1/warnings/{warning_id}")
    assert detail.status_code == 200, detail.text

    # 学生列表应当包含该预警
    lst = await client.get("/api/v1/warnings", params={"size": 50})
    assert lst.status_code == 200, lst.text
    items = lst.json()["items"]
    matched = [it for it in items if it["warning_id"] == warning_id]
    assert matched, f"warning {warning_id} not visible to student001: {items}"


@pytest.mark.asyncio
async def test_publish_warning_dept_scope_only_targets_see(
    client: AsyncClient, seed_warnings_minimum
) -> None:
    """发 dept=CS 的预警；CS 学生能看；MATH 学生看不到。"""
    fixture = seed_warnings_minimum
    await _login(client, "reviewer_school001")

    r = await client.post(
        "/api/v1/admin/warnings",
        json={
            "title": "[CS] 院内电信诈骗专题预警",
            "content": "本院近期发生多起电信诈骗案件，请同学加强防范。",
            "warning_level": 2,
            "push_scope": "DEPARTMENT",
            "target_dept_ids": [fixture["dept_cs_id"]],
        },
    )
    assert r.status_code == 201, r.text
    warning_id = r.json()["warning_id"]

    # CS 学生应该看得到
    await _login(client, "student001")
    lst = await client.get("/api/v1/warnings", params={"size": 50})
    assert lst.status_code == 200, lst.text
    assert any(it["warning_id"] == warning_id for it in lst.json()["items"])

    # MATH 学生看不到
    await _login(client, "student002")
    lst2 = await client.get("/api/v1/warnings", params={"size": 50})
    assert lst2.status_code == 200, lst2.text
    assert not any(it["warning_id"] == warning_id for it in lst2.json()["items"])

    # 直接拿 id 也是 NotFound（不暴露存在性）
    detail = await client.get(f"/api/v1/warnings/{warning_id}")
    assert detail.status_code == 404, detail.text


@pytest.mark.asyncio
async def test_publish_emergency_requires_school_level(
    client: AsyncClient, seed_warnings_minimum
) -> None:
    """reviewer_dept001（role_level=1）发 level=3 → 403（PermissionDenied 紧急预警仅校级）。"""
    await _login(client, "reviewer_dept001")
    r = await client.post(
        "/api/v1/admin/warnings",
        json={
            "title": "院级误发紧急预警",
            "content": "院级管理员尝试发布紧急预警，应被校级权限拦截。",
            "warning_level": 3,
            "push_scope": "FULL_SCHOOL",
        },
    )
    assert r.status_code == 403, r.text
    assert r.json()["code"] == 20002


# ── 追加 / 下线 ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_append_offline_warning_409(
    client: AsyncClient, seed_warnings_minimum
) -> None:
    """先 offline 再 append → 409 WarningOfflineConflict。"""
    await _login(client, "reviewer_school001")
    r = await client.post(
        "/api/v1/admin/warnings",
        json={
            "title": "用于下线测试的预警",
            "content": "正文内容至少十个字以确保校验通过的占位文本。",
            "warning_level": 1,
            "push_scope": "FULL_SCHOOL",
        },
    )
    assert r.status_code == 201, r.text
    warning_id = r.json()["warning_id"]

    off = await client.post(
        f"/api/v1/admin/warnings/{warning_id}/offline",
        json={"reason": "原案件已澄清"},
    )
    assert off.status_code == 200, off.text

    # 已下线再追加 → 409
    ap = await client.post(
        f"/api/v1/admin/warnings/{warning_id}/append",
        json={"appendix": "试图追加但已下线"},
    )
    assert ap.status_code == 409, ap.text
    assert ap.json()["code"] == 40003


@pytest.mark.asyncio
async def test_offline_then_offline_409(
    client: AsyncClient, seed_warnings_minimum
) -> None:
    """连续 offline → 409。"""
    await _login(client, "reviewer_school001")
    r = await client.post(
        "/api/v1/admin/warnings",
        json={
            "title": "用于重复下线的预警",
            "content": "正文内容至少十个字的占位文本以便通过校验。",
            "warning_level": 1,
            "push_scope": "FULL_SCHOOL",
        },
    )
    assert r.status_code == 201, r.text
    warning_id = r.json()["warning_id"]

    off1 = await client.post(
        f"/api/v1/admin/warnings/{warning_id}/offline",
        json={"reason": "首次下线"},
    )
    assert off1.status_code == 200, off1.text

    off2 = await client.post(
        f"/api/v1/admin/warnings/{warning_id}/offline",
        json={"reason": "重复下线"},
    )
    assert off2.status_code == 409, off2.text
    assert off2.json()["code"] == 40003


# ── 权限与参数 ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_student_cannot_publish(
    client: AsyncClient, seed_warnings_minimum
) -> None:
    """student001 调 POST /admin/warnings → 403。"""
    await _login(client, "student001")
    r = await client.post(
        "/api/v1/admin/warnings",
        json={
            "title": "学生越权发布",
            "content": "学生不应能调用管理员接口的内容占位至十字。",
            "warning_level": 1,
            "push_scope": "FULL_SCHOOL",
        },
    )
    assert r.status_code == 403, r.text
    assert r.json()["code"] == 20002


@pytest.mark.asyncio
async def test_warning_create_validates_dept_scope(
    client: AsyncClient, seed_warnings_minimum
) -> None:
    """scope=DEPARTMENT 不传 target_dept_ids → 422。"""
    await _login(client, "reviewer_school001")
    r = await client.post(
        "/api/v1/admin/warnings",
        json={
            "title": "院系范围缺失目标",
            "content": "院系推送但没传 target_dept_ids，应被 422 拒绝。",
            "warning_level": 1,
            "push_scope": "DEPARTMENT",
        },
    )
    assert r.status_code == 422, r.text
    assert r.json()["code"] == 10001
