"""角色权限关联表（PRD 5.3.1 表 5.9）。

复合主键：``(role_id, permission_id)``。
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column

from app.infra.db.base import Base


class RolePermission(Base):
    __tablename__ = "role_permissions"
    __table_args__ = {"comment": "角色权限关联表 - PRD 5.3.1 表 5.9"}

    role_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("roles.role_id", ondelete="CASCADE"), primary_key=True
    )
    permission_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("permissions.permission_id", ondelete="CASCADE"), primary_key=True
    )
    granted_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.current_timestamp()
    )
    granted_by: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=True,
        comment="授予人 user_id（可空）",
    )
