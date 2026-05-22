"""集成：登录全链路 + 攻击向量。

覆盖 PRD 2.7 自检 4 类攻击（伪造 Cookie / 篡改 ticket / CSRF / 替换 session_id）。
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.infra.db.models import Department, Role, User
from app.infra.db.models.user import UserStatus
from app.services import permissions as perm

pytestmark = pytest.mark.integration


@pytest.fixture
async def seed_minimum(db_session) -> None:
    """最小 seed：UNKNOWN 院系 + STUDENT 角色 + 必备权限码。"""
    from app.core.snowflake import next_snowflake_id
    from app.infra.cache.rbac_cache import RBACCache
    from app.infra.db.models import Permission, RolePermission
    from app.infra.repositories.role import RoleRepository

    # 院系
    dept = Department(dept_code="UNKNOWN", dept_name="未指定", dept_level=1, sort_order=0)
    db_session.add(dept)
    await db_session.flush()

    # 角色
    student_role = Role(role_code=Role.CODE_STUDENT, role_name="学生", role_level=1)
    sysadmin_role = Role(role_code=Role.CODE_SYS_ADMIN, role_name="系统管理员", role_level=1)
    db_session.add_all([student_role, sysadmin_role])
    await db_session.flush()

    # 权限码 + RBAC
    p_user_read = Permission(
        permission_code=perm.USER_READ,
        permission_name="用户读",
        resource_type="USER",
        action_type="READ",
    )
    db_session.add(p_user_read)
    await db_session.flush()
    db_session.add(
        RolePermission(role_id=sysadmin_role.role_id, permission_id=p_user_read.permission_id)
    )

    # 测试账号
    db_session.add(
        User(
            user_id=next_snowflake_id(),
            cas_account="student001",
            real_name="张三",
            department_id=dept.dept_id,
            role_id=student_role.role_id,
            status=UserStatus.ACTIVE.value,
        )
    )
    db_session.add(
        User(
            user_id=next_snowflake_id(),
            cas_account="sysadmin001",
            real_name="管理员",
            department_id=dept.dept_id,
            role_id=sysadmin_role.role_id,
            status=UserStatus.ACTIVE.value,
        )
    )
    await db_session.commit()

    # RBAC 缓存预热
    async with __import__("app.infra.db.session", fromlist=["uow"]).uow() as session:
        rrepo = RoleRepository(session)
        mapping = await rrepo.list_role_permissions_full()
    await RBACCache().load(mapping)


@pytest.mark.asyncio
class TestLoginFlow:
    async def test_mock_login_success(self, client: AsyncClient, seed_minimum) -> None:
        resp = await client.post(
            "/api/v1/auth/cas/mock-login",
            json={"cas_account": "student001"},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["cas_account"] == "student001"
        assert body["role_code"] == "STUDENT"

    async def test_csrf_required_on_writes(self, client: AsyncClient, seed_minimum) -> None:
        # 移除 X-Requested-With → 应被 CSRF middleware 拦截
        client.headers.pop("X-Requested-With", None)
        resp = await client.post(
            "/api/v1/auth/cas/mock-login",
            json={"cas_account": "student001"},
        )
        assert resp.status_code == 400
        assert resp.json()["code"] == 10010

    async def test_forged_session_cookie_rejected(self, client: AsyncClient, seed_minimum) -> None:
        """伪造一个 cookie 试图绕开登录。"""
        client.cookies.set("afp_session", "deadbeef-not-a-real-session")
        resp = await client.get("/api/v1/auth/me")
        assert resp.status_code == 401

    async def test_session_replaced_after_login(self, client: AsyncClient, seed_minimum) -> None:
        """登录后 cookie 被服务端覆盖（防会话固定）。"""
        client.cookies.set("afp_session", "stale-session-id")
        resp = await client.post(
            "/api/v1/auth/cas/mock-login",
            json={"cas_account": "student001"},
        )
        assert resp.status_code == 200
        # 服务端 set-cookie 应下发一条新的 36 字符 UUID session_id
        # （httpx jar 可能保留两条同名 cookie，因此遍历查找）
        new_sids = [c.value for c in client.cookies.jar if c.name == "afp_session"]
        assert any(len(v) == 36 and v != "stale-session-id" for v in new_sids), new_sids

    async def test_replay_ticket_rejected(self, client: AsyncClient, seed_minimum) -> None:
        """同一 CAS ticket 二次使用 → CASTicketReplay。

        ``/cas/callback`` 是真实票据进入点（mock-login 端点会自动给每次请求拼
        一个一次性 nonce 以绕开重放保护，便于本地多角色调试）。
        """
        from urllib.parse import quote

        service = "http://localhost:8000/api/v1/auth/cas/callback"
        ticket = "fixed_ticket_for_replay_test"
        # 第一次成功（302 → 工作台）
        resp1 = await client.get(
            f"/api/v1/auth/cas/callback?ticket={ticket}&service={quote(service)}",
            follow_redirects=False,
        )
        assert resp1.status_code in (302, 303), resp1.text
        # 第二次同一 ticket 被去重拒绝
        resp2 = await client.get(
            f"/api/v1/auth/cas/callback?ticket={ticket}&service={quote(service)}",
            follow_redirects=False,
        )
        assert resp2.status_code == 401
        assert resp2.json()["code"] == 20006


@pytest.mark.asyncio
class TestRBAC:
    async def test_student_blocked_from_sysadmin_endpoint(
        self, client: AsyncClient, seed_minimum
    ) -> None:
        resp = await client.post(
            "/api/v1/auth/cas/mock-login",
            json={"cas_account": "student001"},
        )
        assert resp.status_code == 200
        # 学生没 user:read 权限
        resp = await client.get("/api/v1/users")
        assert resp.status_code == 403
        assert resp.json()["code"] == 20002

    async def test_sysadmin_can_list_users(self, client: AsyncClient, seed_minimum) -> None:
        resp = await client.post(
            "/api/v1/auth/cas/mock-login",
            json={"cas_account": "sysadmin001"},
        )
        assert resp.status_code == 200
        resp = await client.get("/api/v1/users")
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["total"] >= 2
