"""预警公告主表（PRD 5.16，UC-03 / UC-07）。

预警等级、推送范围、上下线状态等控制由业务层 :class:`WarningService` 管理。
雪花 ID 与状态机校验由 service 层统一负责，模型层只描述持久化结构。
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, ForeignKey, Index, SmallInteger, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.infra.db.base import Base, TimestampMixin


class WarningLevel:
    """预警等级常量（与 PRD 5.16 一致）。"""

    HINT = 1       # 提示
    WARNING = 2    # 警告
    URGENT = 3     # 紧急

    ALL: frozenset[int] = frozenset({HINT, WARNING, URGENT})


class WarningPushScope:
    """推送范围常量（与 PRD UC-03 一致）。"""

    FULL_SCHOOL = "FULL_SCHOOL"  # 全校推送
    DEPARTMENT = "DEPARTMENT"    # 按院系推送

    ALL: frozenset[str] = frozenset({FULL_SCHOOL, DEPARTMENT})


class WarningStatus:
    """上下线状态常量（与 PRD UC-07 一致）。"""

    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"

    ALL: frozenset[str] = frozenset({ONLINE, OFFLINE})


class WarningNotice(Base, TimestampMixin):
    """预警公告主表。"""

    __tablename__ = "warning_notices"
    __table_args__ = (
        Index("idx_warning_status_published", "status", "published_at"),
        Index("idx_warning_level", "warning_level"),
        Index("idx_warning_publisher", "publisher_id"),
        Index("idx_warning_scope", "push_scope"),
        {"comment": "预警公告主表 PRD UC-03/UC-07"},
    )

    warning_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, comment="雪花算法生成"
    )
    title: Mapped[str] = mapped_column(String(128), nullable=False, comment="预警标题")
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="预警正文")
    warning_level: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        comment="预警等级 1=提示 / 2=警告 / 3=紧急",
    )
    related_case_no: Mapped[str | None] = mapped_column(
        String(32), nullable=True, comment="关联案件编号（可选）"
    )
    publisher_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.user_id", ondelete="RESTRICT"),
        nullable=False,
        comment="发布人 user_id",
    )
    push_scope: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        comment="推送范围 FULL_SCHOOL / DEPARTMENT",
    )
    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default=WarningStatus.ONLINE,
        server_default=WarningStatus.ONLINE,
        comment="状态 ONLINE / OFFLINE",
    )
    appendix: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="追加后续说明（UC-07 步骤 8）"
    )
    published_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=func.current_timestamp(),
        comment="发布时间",
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        nullable=True, comment="过期时间（可选）"
    )
    offline_at: Mapped[datetime | None] = mapped_column(
        nullable=True, comment="下线时间"
    )
    offline_reason: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="下线原因"
    )

    def __repr__(self) -> str:
        return f"<WarningNotice {self.warning_id} L{self.warning_level} [{self.status}]>"
