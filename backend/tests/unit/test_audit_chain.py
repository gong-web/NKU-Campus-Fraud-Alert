"""审计哈希链 + AuditService 验证（重点：篡改一条 → 校验失败）。"""

from __future__ import annotations

import pytest

from app.domain.user_snapshot import UserSnapshot
from app.services.audit_service import _compute_hash


def _make_user() -> UserSnapshot:
    return UserSnapshot(
        user_id=1,
        cas_account="u",
        real_name="u",
        role_id=1,
        role_code="STUDENT",
        department_id=1,
        session_id="s",
        source_ip="127.0.0.1",
        user_agent="ua",
    )


class TestHashChain:
    def test_chain_links(self) -> None:
        p1 = {"log_id": 1, "operator_id": 1, "operation_type": "X"}
        p2 = {"log_id": 2, "operator_id": 1, "operation_type": "Y"}
        h1 = _compute_hash(prev_hash=None, payload=p1)
        h2 = _compute_hash(prev_hash=h1, payload=p2)
        assert h1 != h2
        # 同 prev + 同 payload → 确定性
        assert _compute_hash(prev_hash=h1, payload=p2) == h2

    def test_tampered_breaks(self) -> None:
        p1 = {"log_id": 1, "field": "a"}
        h1 = _compute_hash(prev_hash=None, payload=p1)
        tampered = {"log_id": 1, "field": "b"}
        h_t = _compute_hash(prev_hash=None, payload=tampered)
        assert h1 != h_t


@pytest.mark.asyncio
class TestAuditServiceValidation:
    """SDK 强校验：杜绝写半截日志。"""

    async def test_invalid_op_type_lowercase(self, db_session) -> None:
        from app.exceptions import AuditWriteFailed
        from app.services.audit_service import AuditService

        svc = AuditService()
        with pytest.raises(AuditWriteFailed):
            await svc.write(
                operator=_make_user(),
                op_type="login",  # 非大写
                obj_type="user",
                obj_id="1",
                sync=True,
            )

    async def test_missing_operator_for_login(self, db_session) -> None:
        from app.exceptions import AuditWriteFailed
        from app.services.audit_service import AuditService

        svc = AuditService()
        with pytest.raises(AuditWriteFailed):
            await svc.write(
                operator=None,
                op_type="LOGIN",  # LOGIN 必须带 operator
                obj_type="user",
                obj_id="1",
                sync=True,
            )

    async def test_empty_obj_id(self, db_session) -> None:
        from app.exceptions import AuditWriteFailed
        from app.services.audit_service import AuditService

        svc = AuditService()
        with pytest.raises(AuditWriteFailed):
            await svc.write(
                operator=_make_user(),
                op_type="LOGIN",
                obj_type="user",
                obj_id="",
                sync=True,
            )
