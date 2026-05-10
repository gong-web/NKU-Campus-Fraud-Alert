"""账号管理（UC-10）业务流程：CRUD + 角色变更 + 停用 + CSV 导入。"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.infra.db.models.user import UserStatus

pytestmark = pytest.mark.integration


@pytest.fixture
async def seed_full(db_session) -> None:
    """完整 seed：角色 + 完整权限矩阵 + 测试账号。"""
    from app.core.snowflake import next_snowflake_id
    from app.infra.cache.rbac_cache import RBACCache
    from app.infra.db.models import (
        Department,
        Permission,
        Role,
        RolePermission,
        User,
    )
    from app.infra.repositories.role import RoleRepository
    from app.services import permissions as perm

    cs = Department(dept_code="CS", dept_name="计算机", dept_level=1, sort_order=0)
    unknown = Department(dept_code="UNKNOWN", dept_name="未指定", dept_level=1, sort_order=0)
    db_session.add_all([cs, unknown])
    await db_session.flush()

    student_role = Role(role_code="STUDENT", role_name="学生", role_level=1)
    sysadmin_role = Role(role_code="SYS_ADMIN", role_name="系统管理员", role_level=1)
    db_session.add_all([student_role, sysadmin_role])
    await db_session.flush()

    needed = [
        perm.USER_READ,
        perm.USER_CREATE,
        perm.USER_UPDATE,
        perm.USER_DISABLE,
        perm.USER_BATCH_IMPORT,
    ]
    perms = []
    for code in needed:
        resource, action = code.split(":", 1)
        p = Permission(
            permission_code=code,
            permission_name=code,
            resource_type=resource.upper(),
            action_type=action.upper(),
        )
        db_session.add(p)
        perms.append(p)
    await db_session.flush()

    for p in perms:
        db_session.add(RolePermission(role_id=sysadmin_role.role_id, permission_id=p.permission_id))
    await db_session.flush()

    db_session.add(
        User(
            user_id=next_snowflake_id(),
            cas_account="sysadmin001",
            real_name="管理员",
            department_id=unknown.dept_id,
            role_id=sysadmin_role.role_id,
            status=UserStatus.ACTIVE.value,
        )
    )
    db_session.add(
        User(
            user_id=next_snowflake_id(),
            cas_account="student001",
            real_name="张三",
            department_id=cs.dept_id,
            role_id=student_role.role_id,
            status=UserStatus.ACTIVE.value,
        )
    )
    await db_session.commit()

    from app.infra.db.session import uow as _uow

    async with _uow() as s:
        repo = RoleRepository(s)
        mapping = await repo.list_role_permissions_full()
    await RBACCache().load(mapping)


@pytest.mark.asyncio
class TestUserCRUD:
    async def test_create_then_disable(self, client: AsyncClient, seed_full) -> None:
        r = await client.post("/api/v1/auth/cas/mock-login", json={"cas_account": "sysadmin001"})
        assert r.status_code == 200, r.text

        r = await client.post(
            "/api/v1/users",
            json={
                "cas_account": "newcomer001",
                "real_name": "新生",
                "department_id": 1,
                "role_id": 1,
            },
        )
        assert r.status_code == 201, r.text
        new_uid = r.json()["user_id"]

        r = await client.get(f"/api/v1/users/{new_uid}")
        assert r.status_code == 200
        assert r.json()["cas_account"] == "newcomer001"

        r = await client.patch(f"/api/v1/users/{new_uid}", json={"status": 2, "reason": "毕业离校"})
        assert r.status_code == 200, r.text

        r = await client.get(f"/api/v1/users/{new_uid}")
        assert r.json()["status"] == 2

    async def test_duplicate_conflict(self, client: AsyncClient, seed_full) -> None:
        await client.post("/api/v1/auth/cas/mock-login", json={"cas_account": "sysadmin001"})
        r = await client.post(
            "/api/v1/users",
            json={
                "cas_account": "sysadmin001",
                "real_name": "重复",
                "department_id": 1,
                "role_id": 1,
            },
        )
        assert r.status_code == 409
        assert r.json()["code"] == 10003

    async def test_csv_dry_run(self, client: AsyncClient, seed_full) -> None:
        await client.post("/api/v1/auth/cas/mock-login", json={"cas_account": "sysadmin001"})
        csv_text = (
            "cas_account,real_name,dept_code,role_code\n"
            "stu_a,新生 A,CS,STUDENT\n"
            "stu_b,新生 B,CS,STUDENT\n"
        )
        r = await client.post("/api/v1/users/import", json={"csv_text": csv_text, "dry_run": True})
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["ok"] is True
        assert body.get("dry_run") is True

    async def test_csv_invalid_returns_errors(self, client: AsyncClient, seed_full) -> None:
        await client.post("/api/v1/auth/cas/mock-login", json={"cas_account": "sysadmin001"})
        # 缺列
        r = await client.post(
            "/api/v1/users/import",
            json={"csv_text": "cas_account,real_name\nx,y\n", "dry_run": True},
        )
        assert r.status_code == 200
        assert r.json()["ok"] is False

    async def test_invalid_role_id_rejected(self, client: AsyncClient, seed_full) -> None:
        await client.post("/api/v1/auth/cas/mock-login", json={"cas_account": "sysadmin001"})
        # 拿 student 的 user_id
        listed = await client.get("/api/v1/users", params={"keyword": "student001"})
        students = [x for x in listed.json()["items"] if x["cas_account"] == "student001"]
        assert students, listed.json()
        target = students[0]["user_id"]

        # 改成不存在的 role_id 应返回 422 / 400 / 422
        r = await client.patch(f"/api/v1/users/{target}", json={"role_id": 999_999})
        assert r.status_code in (400, 404, 422)
