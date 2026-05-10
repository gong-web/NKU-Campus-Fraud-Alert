"""权限表（PRD 5.3.1 表 5.8）。"""

from __future__ import annotations

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.infra.db.base import Base


class Permission(Base):
    """权限码：``<resource>:<action>``，如 ``user:create`` / ``warning:publish``。"""

    __tablename__ = "permissions"
    __table_args__ = {"comment": "权限表 - PRD 5.3.1 表 5.8"}

    permission_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    permission_code: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        comment="如 REPORT:CREATE / WARNING:PUBLISH（小写也行：report:create）",
    )
    permission_name: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_type: Mapped[str] = mapped_column(
        String(32), nullable=False, comment="REPORT / WARNING / KB ..."
    )
    action_type: Mapped[str] = mapped_column(
        String(16), nullable=False, comment="CREATE / READ / UPDATE / DELETE"
    )
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    def __repr__(self) -> str:
        return f"<Permission {self.permission_code}>"
