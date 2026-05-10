"""SQLAlchemy Declarative 基类与共享元数据。

约定（见 ``docs/conventions.md``）
---------------------------------
- 主键命名：``<entity>_id``。
- 时间字段：``created_at`` / ``updated_at`` / ``last_active_at`` 等以 ``_at`` 结尾。
- 外键字段：以 ``_id`` 结尾。
- 布尔字段：以 ``is_`` 开头（DB 里仍然是 ``TINYINT(1)``）。

命名约定让 Alembic 自动生成的 ``constraint`` 名字可读，避免 ``unique_4f3a`` 之类。
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import MetaData, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Alembic 自动生成约束名规则
NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_N_name)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """所有 ORM 模型的基类。"""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)

    def to_dict(self, *, exclude: set[str] | None = None) -> dict[str, Any]:
        """便利方法：把模型变成 dict（不含关系字段，仅列）。"""
        exclude = exclude or set()
        return {
            c.name: getattr(self, c.name) for c in self.__table__.columns if c.name not in exclude
        }


class TimestampMixin:
    """``created_at`` / ``updated_at``。MySQL 用 CURRENT_TIMESTAMP。"""

    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(tz=UTC),
        server_default=func.current_timestamp(),
        nullable=False,
        comment="创建时间（UTC）",
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(tz=UTC),
        onupdate=lambda: datetime.now(tz=UTC),
        server_default=func.current_timestamp(),
        nullable=False,
        comment="最近更新时间（UTC）",
    )
