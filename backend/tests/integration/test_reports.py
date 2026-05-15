"""集成：上报提交与草稿管理（UC-01 / UC-02）。

覆盖：
- 正常路径：学生提交上报 → 201 + 案件编号格式正确
- 失败路径：无效诈骗类型 → 422 / 30004
- 失败路径：未登录访问 → 401 / 20001
- 正常路径：创建草稿 → 201 + draft_id
- 失败路径：跨用户访问草稿 → 403 / 20002
"""

from __future__ import annotations

import re

import pytest
from httpx import AsyncClient

from app.infra.db.models import Department, FraudType, Permission, Role, RolePermission, User
from app.infra.db.models.user import UserStatus
from app.services import permissions as perm

pytestmark = pytest.mark.integration

# ── 测试 seed ────────────────────────────────────────────────────────


@pytest.fixture
async def seed_reports(db_session) -> None:
    """最小 seed：UNKNOWN 院系 + STUDENT 角色（含 report:create / report:read_own）+ 1 条诈骗类型。

    mock-login 会自动注册未知 cas_account 为 STUDENT，因此不需要预建用户记录。
    两名测试用户（student_alice / student_bob）由各用例的 mock-login 自动注册。
    """
    from app.infra.cache.rbac_cache import RBACCache
    from app.infra.repositories.role import RoleRepository

    # 1. 院系
    dept = Department(dept_code="UNKNOWN", dept_name="未指定", dept_level=1, sort_order=0)
    db_session.add(dept)
    await db_session.flush()

    # 2. STUDENT 角色
    student_role = Role(role_code=Role.CODE_STUDENT, role_name="学生", role_level=1)
    db_session.add(student_role)
    await db_session.flush()

    # 3. 权限码
    p_create = Permission(
        permission_code=perm.REPORT_CREATE,
        permission_name="提交上报",
        resource_type="REPORT",
        action_type="CREATE",
    )
    p_read_own = Permission(
        permission_code=perm.REPORT_READ_OWN,
        permission_name="查看本人上报",
        resource_type="REPORT",
        action_type="READ",
    )
    db_session.add_all([p_create, p_read_own])
    await db_session.flush()

    # 4. 角色-权限关联
    db_session.add_all(
        [
            RolePermission(
                role_id=student_role.role_id, permission_id=p_create.permission_id
            ),
            RolePermission(
                role_id=student_role.role_id, permission_id=p_read_own.permission_id
            ),
        ]
    )

    # 5. 诈骗类型（type_id 由 SQLite autoincrement 分配，从 1 开始）
    db_session.add(
        FraudType(
            type_code="TELECOM_FRAUD",
            type_name="电信诈骗",
            description="通过电话、短信实施的诈骗",
            is_active=True,
            sort_order=1,
        )
    )

    await db_session.commit()

    # 6. RBAC 缓存预热（写入 fakeredis，供 require_permission O(1) 查询）
    async with __import__("app.infra.db.session", fromlist=["uow"]).uow() as session:
        rrepo = RoleRepository(session)
        mapping = await rrepo.list_role_permissions_full()
    await RBACCache().load(mapping)


# ── 上报提交（POST /api/v1/reports）────────────────────────────────


@pytest.mark.asyncio
class TestCreateReport:
    async def test_create_report_success(
        self, client: AsyncClient, seed_reports
    ) -> None:
        """学生提交完整上报 → 201，返回有效案件编号和 PENDING 状态。"""
        # 登录（mock 模式：cas_account 即票据，未知账号自动注册为 STUDENT）
        r = await client.post(
            "/api/v1/auth/cas/mock-login",
            json={"cas_account": "rpt_alice_001"},
        )
        assert r.status_code == 200, r.text

        # 提交上报
        r = await client.post(
            "/api/v1/reports",
            json={
                "title": "收到可疑退款短信",
                "description": (
                    "收到自称银行客服的短信，要求点击链接退款，"
                    "链接疑似钓鱼网站，已截图保存备查。"
                ),
                "fraud_type_id": 1,  # 对应 seed 中 TELECOM_FRAUD
                "incident_date": "2026-05-01",
                "is_anonymous": False,
            },
        )
        assert r.status_code == 201, r.text
        body = r.json()

        # 案件编号格式：YYYY-DEPTCODE-NNNNNN
        assert "case_id" in body
        assert "case_no" in body
        assert re.match(r"^\d{4}-[A-Z]+-\d{6}$", body["case_no"]), body["case_no"]
        assert body["status"] == "PENDING"
        assert body["fraud_type_id"] == 1
        assert body["is_anonymous"] is False

    async def test_create_report_invalid_fraud_type(
        self, client: AsyncClient, seed_reports
    ) -> None:
        """提交时指定不存在的诈骗类型 → 422，应用错误码 30004。"""
        r = await client.post(
            "/api/v1/auth/cas/mock-login",
            json={"cas_account": "rpt_alice_002"},
        )
        assert r.status_code == 200, r.text

        r = await client.post(
            "/api/v1/reports",
            json={
                "title": "测试无效类型",
                "description": "这是一段用于测试的详细描述文字，超过十个字。",
                "fraud_type_id": 999999,  # 不存在的类型 ID
                "incident_date": "2026-05-01",
            },
        )
        assert r.status_code == 422, r.text
        assert r.json()["code"] == 30004

    async def test_create_report_unauthenticated(
        self, client: AsyncClient, seed_reports
    ) -> None:
        """未登录直接调用上报接口 → 401，应用错误码 20001。"""
        r = await client.post(
            "/api/v1/reports",
            json={
                "title": "未登录提交",
                "description": "这是一段用于测试的详细描述文字，超过十个字。",
                "fraud_type_id": 1,
                "incident_date": "2026-05-01",
            },
        )
        assert r.status_code == 401, r.text
        assert r.json()["code"] == 20001


# ── 草稿管理（POST /api/v1/drafts, GET /api/v1/drafts/{id}）────────


@pytest.mark.asyncio
class TestDraftCRUD:
    async def test_create_and_get_draft(
        self, client: AsyncClient, seed_reports
    ) -> None:
        """学生创建草稿 → 201；再查询同一草稿 → 200，内容一致。"""
        r = await client.post(
            "/api/v1/auth/cas/mock-login",
            json={"cas_account": "dft_alice_001"},
        )
        assert r.status_code == 200, r.text

        # 创建草稿（所有字段可选）
        r = await client.post(
            "/api/v1/drafts",
            json={"title": "刷单兼职诈骗草稿", "is_anonymous": True},
        )
        assert r.status_code == 201, r.text
        draft = r.json()
        assert "draft_id" in draft
        assert draft["title"] == "刷单兼职诈骗草稿"
        assert draft["is_anonymous"] is True

        # 按 ID 查询同一草稿
        r = await client.get(f"/api/v1/drafts/{draft['draft_id']}")
        assert r.status_code == 200, r.text
        assert r.json()["draft_id"] == draft["draft_id"]

    async def test_other_user_cannot_access_draft(
        self, client: AsyncClient, seed_reports
    ) -> None:
        """用户 B 不能查看用户 A 的草稿 → 403，应用错误码 20002。"""
        # 用户 A 登录并创建草稿
        r = await client.post(
            "/api/v1/auth/cas/mock-login",
            json={"cas_account": "dft_alice_002"},
        )
        assert r.status_code == 200, r.text

        r = await client.post("/api/v1/drafts", json={"title": "用户 A 的私有草稿"})
        assert r.status_code == 201, r.text
        draft_id = r.json()["draft_id"]

        # 用户 B 登录（不同 cas_account → 新会话覆盖旧会话 cookie）
        r = await client.post(
            "/api/v1/auth/cas/mock-login",
            json={"cas_account": "dft_bob_002"},
        )
        assert r.status_code == 200, r.text

        # 用户 B 尝试访问用户 A 的草稿
        r = await client.get(f"/api/v1/drafts/{draft_id}")
        assert r.status_code == 403, r.text
        assert r.json()["code"] == 20002
