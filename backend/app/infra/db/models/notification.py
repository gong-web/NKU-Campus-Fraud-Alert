"""站内通知表（PRD 5.3.5 表 5.26）。

虽然通知主流程由其他模块完成（事件审核、预警发布等触发），但为保证数据
模型一致性，本骨架先把表建起来——其它组员只需要写 ``NotificationService``。
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, ForeignKey, Index, SmallInteger, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.infra.db.base import Base


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (
        Index("idx_notif_user_read_time", "recipient_id", "is_read", "created_at"),
        Index("idx_notif_type", "type"),
        {"comment": "站内通知表 - PRD 5.3.5 表 5.26"},
    )

    notification_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    recipient_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.user_id", ondelete="RESTRICT"),
        nullable=False,
    )
    type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        comment="如 REPORT_RESOLVED / WARNING_PUSH / QUIZ_ASSIGNED",
    )
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    content: Mapped[str] = mapped_column(String(512), nullable=False)
    related_object_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    related_object_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    is_read: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=0, server_default="0"
    )
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.current_timestamp()
    )
    read_at: Mapped[datetime | None] = mapped_column(nullable=True)
