"""系统参数表（PRD 5.3.5 表 5.29）。"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, ForeignKey, Integer, SmallInteger, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.infra.db.base import Base


class SystemConfig(Base):
    __tablename__ = "system_configs"
    __table_args__ = {"comment": "系统参数表 - PRD 5.3.5 表 5.29"}

    config_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    config_key: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, comment="参数键名（业务约定唯一）"
    )
    config_value: Mapped[str] = mapped_column(Text, nullable=False)
    value_type: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="STRING",
        server_default="STRING",
        comment="STRING / INT / BOOLEAN / JSON",
    )
    is_sensitive: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=0,
        server_default="0",
        comment="为 1 时审计日志中遮蔽其值",
    )
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    updated_by: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )
