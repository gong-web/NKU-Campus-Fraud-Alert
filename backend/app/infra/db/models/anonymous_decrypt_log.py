"""匿名身份解密授权日志（PRD ER 图扩展字段）。

UC-10 备选 A2"司法协助查询匿名上报者身份"——平台**最高敏**操作。

每次请求一条授权记录：
- 5 分钟解密窗口（``expires_at``）
- 关联到一条审计日志（``audit_log_id``）
- 通过站内信 + 备用邮箱告警**全员** SysAdmin
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.infra.db.base import Base


class AnonymousDecryptLog(Base):
    __tablename__ = "anonymous_decrypt_logs"
    __table_args__ = {"comment": "匿名身份解密授权日志（UC-10 备选 A2）"}

    decrypt_log_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    report_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    requester_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.user_id", ondelete="RESTRICT"),
        nullable=False,
        comment="申请人（必为 SysAdmin）",
    )
    approver_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.user_id", ondelete="RESTRICT"),
        nullable=True,
        comment="如启用书面审批流，记录批准人",
    )
    judicial_doc_no: Mapped[str] = mapped_column(String(64), nullable=False, comment="协查文书编号")
    reason: Mapped[str] = mapped_column(Text, nullable=False, comment="申请理由")
    related_case_no: Mapped[str | None] = mapped_column(
        String(32), nullable=True, comment="关联事件 case_no"
    )
    expires_at: Mapped[datetime] = mapped_column(
        nullable=False,
        comment="解密窗口失效时刻（默认 ``now() + 5min``）",
    )
    audit_log_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("audit_logs.log_id", ondelete="RESTRICT"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.current_timestamp()
    )
