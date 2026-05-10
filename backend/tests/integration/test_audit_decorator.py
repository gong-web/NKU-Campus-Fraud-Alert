"""审计 SDK 装饰器 + fallback 路径集成测试。"""

from __future__ import annotations

import pytest
from sqlalchemy import select

from app.domain.user_snapshot import UserSnapshot
from app.exceptions import AuditWriteFailed
from app.infra.db.models import AuditLog
from app.infra.db.session import uow
from app.services.audit_service import AuditService, audit_logged

pytestmark = pytest.mark.integration


def _make_user(uid: int = 1, role: str = "STUDENT") -> UserSnapshot:
    return UserSnapshot(
        user_id=uid,
        cas_account=f"u{uid}",
        real_name=f"u{uid}",
        role_id=1,
        role_code=role,
        department_id=1,
        session_id="s",
        source_ip="127.0.0.1",
        user_agent="ua",
    )


@pytest.mark.asyncio
class TestAuditDecorator:
    async def test_decorator_writes_log(self, db_session) -> None:
        del db_session  # 确保 engine 已 patched

        class _Svc:
            # sync=True：装饰器场景下要求强一致写库，便于测试断言
            @audit_logged(op_type="EXAMPLE_THING", obj_type="thing", sync=True)
            async def do(self, *, obj_id: int, current: UserSnapshot) -> dict[str, int]:
                del current
                return {"result": obj_id * 2}

        result = await _Svc().do(obj_id=21, current=_make_user())
        assert result == {"result": 42}

        async with uow() as session:
            rows = (
                (
                    await session.execute(
                        select(AuditLog).where(AuditLog.operation_type == "EXAMPLE_THING")
                    )
                )
                .scalars()
                .all()
            )
        assert len(rows) >= 1
        assert any(r.object_id == "21" for r in rows)

    async def test_decorator_requires_user_snapshot(self) -> None:
        class _Svc:
            @audit_logged(op_type="X", obj_type="x")
            async def do(self, *, obj_id: int, current: object) -> int:
                del current
                return obj_id

        with pytest.raises(AuditWriteFailed):
            await _Svc().do(obj_id=1, current="not-a-snapshot")  # type: ignore[arg-type]

    async def test_sync_write_in_session(self, db_session) -> None:
        """同事务写审计：commit 后能查到。"""
        svc = AuditService()
        log_id = await svc.write(
            operator=_make_user(role="SYS_ADMIN"),
            op_type="LOGIN",
            obj_type="user",
            obj_id="42",
            sync=True,
            session=db_session,
        )
        assert log_id is not None
        # 同 session 中可见
        found = (
            await db_session.execute(select(AuditLog).where(AuditLog.log_id == log_id))
        ).scalar_one_or_none()
        assert found is not None
        assert found.operation_type == "LOGIN"

    async def test_chain_links_increment(self, db_session) -> None:
        """两条审计链式哈希：第二条的 prev_hash == 第一条的 this_hash。"""
        svc = AuditService()
        log_id_1 = await svc.write(
            operator=_make_user(),
            op_type="LOGIN",
            obj_type="user",
            obj_id="1",
            sync=True,
            session=db_session,
        )
        log_id_2 = await svc.write(
            operator=_make_user(),
            op_type="LOGOUT",
            obj_type="user",
            obj_id="1",
            sync=True,
            session=db_session,
        )
        l1 = (
            await db_session.execute(select(AuditLog).where(AuditLog.log_id == log_id_1))
        ).scalar_one()
        l2 = (
            await db_session.execute(select(AuditLog).where(AuditLog.log_id == log_id_2))
        ).scalar_one()
        assert l1.this_hash is not None
        assert l2.prev_hash == l1.this_hash
