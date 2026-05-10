"""会话表（PRD 5.3.5 表 5.28）。

注意：
- 主键 ``session_id`` 是 ``CHAR(36)`` 的 UUIDv4（防会话固定）。
- 真正的"在线会话"在 Redis 里（TTL 滑动），本表是**审计/查询副本**——
  方便 SysAdmin 在管理页面看到"谁在哪台机器登录了"以及"何时被吊销"。
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.infra.db.base import Base


class SessionRecord(Base):
    """落库的会话记录（不替代 Redis 在线 session）。"""

    __tablename__ = "sessions"
    __table_args__ = (
        Index("idx_session_user_id", "user_id"),
        Index("idx_session_expires_at", "expires_at"),
        {"comment": "会话表 - PRD 5.3.5 表 5.28"},
    )

    session_id: Mapped[str] = mapped_column(String(36), primary_key=True, comment="UUIDv4")
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.user_id", ondelete="RESTRICT"),
        nullable=False,
    )
    cas_ticket: Mapped[str | None] = mapped_column(
        String(128), nullable=True, comment="CAS ServiceTicket 缓存（debug 用）"
    )
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.current_timestamp()
    )
    last_active_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.current_timestamp()
    )
    expires_at: Mapped[datetime] = mapped_column(
        nullable=False, comment="过期时间（默认 30 分钟无操作）"
    )
    source_ip: Mapped[str] = mapped_column(String(45), nullable=False)
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_revoked: Mapped[bool] = mapped_column(
        nullable=False, default=False, server_default="0", comment="被强制下线"
    )
