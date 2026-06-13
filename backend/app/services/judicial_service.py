"""司法协助查询（UC-10 备选 A2）—— 全平台最高敏操作。

PRD 3.4 节关键约束
-----------------
- 强双因素：填写"协查文书编号 + 申请理由 + 关联事件 case_no"。
- 解密窗口 5 分钟（``settings.judicial.decrypt_window_seconds``）。
- 解密身份**水印**显示（操作人 + 时间）—— 由前端实施；本服务在响应中
  返回 ``watermark_text`` 元数据。
- 每次申请同步审计 ``DECRYPT_ANONYMOUS_REQUEST``，每次实际解密同步审计
  ``DECRYPT_ANONYMOUS``。
- 解密结果触发**全员 SysAdmin 站内信告警**（接通知服务后实现，本服务
  暴露 hook）。
- 匿名身份读取统一使用上报流程写入的 ``case_anonymous_reporters``。
- 接口仍受 ``judicial:request_decrypt`` 权限、5 分钟窗口和审计日志约束。
"""

from __future__ import annotations

import base64
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select

from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.security import decrypt_field
from app.core.snowflake import next_snowflake_id
from app.domain.user_snapshot import UserSnapshot
from app.exceptions import (
    JudicialBadRequest,
    JudicialWindowExpired,
    NotFound,
    PermissionDenied,
)
from app.infra.db.models import AnonymousDecryptLog, CaseAnonymousReporter, User
from app.infra.db.session import uow
from app.services.audit_service import get_audit_service

logger = get_logger(__name__)


class JudicialService:
    def __init__(self) -> None:
        self._audit = get_audit_service()
        self._window_s = get_settings().judicial.decrypt_window_seconds

    # ── Step 1：发起申请 ───────────────────────────────────────
    async def request_decryption(
        self,
        *,
        operator: UserSnapshot,
        report_id: int,
        judicial_doc_no: str,
        reason: str,
        related_case_no: str | None = None,
    ) -> dict[str, Any]:
        """SysAdmin 申请解密。"""
        if not operator.is_sysadmin:
            raise PermissionDenied("仅系统管理员可发起司法协助查询")
        judicial_doc_no = judicial_doc_no.strip()
        reason = reason.strip()
        if not judicial_doc_no or len(judicial_doc_no) > 64:
            raise JudicialBadRequest("协查文书编号缺失或过长")
        if not reason:
            raise JudicialBadRequest("申请理由必填")

        now = datetime.now(tz=UTC)
        expires_at = now + timedelta(seconds=self._window_s)

        async with uow() as session:
            audit_log_id = await self._audit.write(
                operator=operator,
                op_type="DECRYPT_ANONYMOUS_REQUEST",
                obj_type="report",
                obj_id=str(report_id),
                after={
                    "judicial_doc_no": judicial_doc_no,
                    "reason": reason,
                    "related_case_no": related_case_no,
                    "expires_at": expires_at.isoformat(),
                },
                sync=True,
                session=session,
            )
            assert audit_log_id is not None

            log_row = AnonymousDecryptLog(
                decrypt_log_id=next_snowflake_id(),
                report_id=report_id,
                requester_id=operator.user_id,
                approver_id=None,
                judicial_doc_no=judicial_doc_no,
                reason=reason,
                related_case_no=related_case_no,
                expires_at=expires_at,
                audit_log_id=audit_log_id,
            )
            session.add(log_row)
            await session.flush()
            decrypt_log_id = log_row.decrypt_log_id

        # 全员告警 —— 通知服务接好后调用；现在只打日志
        logger.warning(
            "judicial_request_filed_notify_all_sysadmins",
            decrypt_log_id=decrypt_log_id,
            requester=operator.cas_account,
            doc_no=judicial_doc_no,
            related_case_no=related_case_no,
        )

        return {
            "decrypt_log_id": decrypt_log_id,
            "expires_at": expires_at.isoformat(),
            "window_seconds": self._window_s,
        }

    # ── Step 2：在窗口内解密 ──────────────────────────────────
    async def decrypt(self, *, operator: UserSnapshot, decrypt_log_id: int) -> dict[str, Any]:
        """实际执行解密，仅在窗口内有效。"""
        if not operator.is_sysadmin:
            raise PermissionDenied("仅系统管理员可执行解密")

        async with uow() as session:
            log_row = await session.get(AnonymousDecryptLog, decrypt_log_id)
            if log_row is None:
                raise NotFound("解密授权记录不存在")
            if log_row.requester_id != operator.user_id:
                raise PermissionDenied("仅原申请人可在窗口内解密")
            now = datetime.now(tz=UTC)
            if now >= log_row.expires_at.replace(tzinfo=UTC):
                raise JudicialWindowExpired()

            mapping = (
                await session.execute(
                    select(CaseAnonymousReporter).where(
                        CaseAnonymousReporter.case_id == log_row.report_id
                    )
                )
            ).scalar_one_or_none()
            if mapping is None:
                raise NotFound("该事件无匿名映射记录（可能不是匿名上报）")

            real_uid_bytes = decrypt_field(mapping.reporter_user_id_enc)
            try:
                real_uid = int(real_uid_bytes.decode("utf-8"))
            except ValueError as exc:
                raise NotFound("匿名映射数据损坏") from exc
            target = await session.get(User, real_uid)
            if target is None:
                raise NotFound("匿名上报者账号不存在或已注销")

            await self._audit.write(
                operator=operator,
                op_type="DECRYPT_ANONYMOUS",
                obj_type="report",
                obj_id=str(log_row.report_id),
                after={
                    "decrypt_log_id": decrypt_log_id,
                    "revealed_user_id": real_uid,
                    "judicial_doc_no": log_row.judicial_doc_no,
                },
                sync=True,
                session=session,
            )

        watermark = (
            f"{operator.cas_account} · {operator.real_name} · "
            f"{now.isoformat()} · {log_row.judicial_doc_no}"
        )
        return {
            "report_id": log_row.report_id,
            "user_id": target.user_id,
            "real_name": target.real_name,
            "cas_account": target.cas_account,
            "watermark_text": watermark,
            "expires_at": log_row.expires_at.isoformat(),
        }


# ── 工具：seed 时给"匿名映射"造数据用 ─────────────────────────
def encode_user_id_for_anonymous(user_id: int) -> bytes:
    """把 user_id 序列化成 plaintext bytes（写入前再 AES-GCM 加密）。"""
    return str(user_id).encode("utf-8")


def encode_b64_for_test(payload: bytes) -> str:  # pragma: no cover - 仅测试用
    return base64.b64encode(payload).decode("ascii")
