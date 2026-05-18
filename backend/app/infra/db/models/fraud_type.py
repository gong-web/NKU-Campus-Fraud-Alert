"""诈骗类型字典表（UC-01）。"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, Integer, SmallInteger, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.infra.db.base import Base


class FraudType(Base):
    """8 类诈骗类型预置数据（可扩展）。"""

    __tablename__ = "fraud_types"
    __table_args__ = {"comment": "诈骗类型字典表 PRD UC-01"}

    type_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    type_code: Mapped[str] = mapped_column(
        String(32), unique=True, nullable=False, index=True, comment="类型编码（大写_下划线）"
    )
    type_name: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="1"
    )
    sort_order: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=0, server_default="0"
    )
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.current_timestamp()
    )

    def __repr__(self) -> str:
        return f"<FraudType {self.type_code}>"
