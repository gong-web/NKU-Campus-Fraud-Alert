"""用户表（PRD 5.3.1 表 5.5）。

最重要的两件事：
1. 手机号 / 邮箱使用 :class:`EncryptedBinary`（AES-256-GCM）落库；业务层无感知。
2. 用 ``status`` 软删除；**禁止物理 DELETE**——审计可追溯。
"""

from __future__ import annotations

from datetime import datetime
from enum import IntEnum

from sqlalchemy import BigInteger, ForeignKey, Index, Integer, SmallInteger, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.infra.db.base import Base
from app.infra.db.types import EncryptedBinary


class UserStatus(IntEnum):
    """User.status 枚举（与 PRD 5.3.1 表 5.5 一致）。"""

    ACTIVE = 1
    DISABLED = 2
    DEREGISTERED = 3


class User(Base):
    """系统所有操作的责任主体（PRD E01）。"""

    __tablename__ = "users"
    __table_args__ = (
        Index("idx_user_dept_role", "department_id", "role_id"),
        Index("idx_user_status", "status"),
        {"comment": "用户表 - PRD 5.3.1 表 5.5"},
    )

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="雪花算法生成")
    cas_account: Mapped[str] = mapped_column(
        String(32),
        unique=True,
        nullable=False,
        index=True,
        comment="CAS 学号或工号（业务唯一键）",
    )
    real_name: Mapped[str] = mapped_column(String(64), nullable=False, comment="真实姓名")
    department_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("departments.dept_id", ondelete="RESTRICT"),
        nullable=False,
    )
    role_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("roles.role_id", ondelete="RESTRICT"),
        nullable=False,
        default=1,
        server_default="1",
        comment="默认 1=学生",
    )
    email_encrypted: Mapped[str | None] = mapped_column(
        EncryptedBinary(255), nullable=True, comment="AES-256-GCM 加密的邮箱（L3）"
    )
    phone_encrypted: Mapped[str | None] = mapped_column(
        EncryptedBinary(96), nullable=True, comment="AES-256-GCM 加密的手机号（L3）"
    )
    avatar_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=UserStatus.ACTIVE.value,
        server_default=str(UserStatus.ACTIVE.value),
        comment="1=正常 / 2=已停用 / 3=已注销",
    )
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.current_timestamp()
    )
    last_login_at: Mapped[datetime | None] = mapped_column(nullable=True)
    last_login_ip: Mapped[str | None] = mapped_column(
        String(45), nullable=True, comment="兼容 IPv6"
    )

    # ── 便利属性 ─────────────────────────────────────────────
    @property
    def is_active(self) -> bool:
        return self.status == UserStatus.ACTIVE.value

    @property
    def is_disabled(self) -> bool:
        return self.status == UserStatus.DISABLED.value

    def __repr__(self) -> str:
        return f"<User {self.cas_account} ({self.user_id})>"
