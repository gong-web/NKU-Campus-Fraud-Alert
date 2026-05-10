"""角色表（PRD 5.3.1 表 5.7）。"""

from __future__ import annotations

from datetime import datetime
from typing import ClassVar

from sqlalchemy import Integer, SmallInteger, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.infra.db.base import Base


class Role(Base):
    """RBAC 中的角色实体。

    ``role_code`` 取值：``STUDENT`` / ``REVIEWER`` / ``SYS_ADMIN``。
    审核管理员的院系级（``role_level=1``）与校级（``role_level=2``）共享
    同一 role_code（``REVIEWER``），区别仅在 ``role_level`` —— 因此唯一键
    是 ``(role_code, role_level)`` 复合而非单列。
    """

    __tablename__ = "roles"
    __table_args__ = (
        UniqueConstraint("role_code", "role_level", name="uq_roles_role_code_role_level"),
        {"comment": "角色表 - PRD 5.3.1 表 5.7"},
    )

    CODE_STUDENT: ClassVar[str] = "STUDENT"
    CODE_REVIEWER: ClassVar[str] = "REVIEWER"
    CODE_SYS_ADMIN: ClassVar[str] = "SYS_ADMIN"

    role_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    role_code: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        comment="STUDENT / REVIEWER / SYS_ADMIN",
    )
    role_name: Mapped[str] = mapped_column(String(64), nullable=False, comment="中文名称")
    role_level: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=1,
        server_default="1",
        comment="REVIEWER 时 1=院系级、2=校级；其它角色固定为 1",
    )
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.current_timestamp()
    )

    def __repr__(self) -> str:
        return f"<Role {self.role_code}.L{self.role_level}>"
