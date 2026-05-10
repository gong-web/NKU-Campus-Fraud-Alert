"""用户管理 schemas。"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.infra.db.models.user import UserStatus


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    cas_account: str
    real_name: str
    department_id: int
    role_id: int
    status: int
    created_at: datetime | None = None
    last_login_at: datetime | None = None


class UserCreateIn(BaseModel):
    cas_account: str = Field(min_length=1, max_length=32)
    real_name: str = Field(min_length=1, max_length=64)
    department_id: int = Field(ge=1)
    role_id: int = Field(ge=1)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, pattern=r"^1[3-9]\d{9}$")


class UserUpdateIn(BaseModel):
    """部分更新（PATCH）。"""

    role_id: int | None = Field(default=None, ge=1)
    status: int | None = Field(
        default=None, ge=int(UserStatus.ACTIVE.value), le=int(UserStatus.DEREGISTERED.value)
    )
    reason: str | None = Field(default=None, max_length=255)


class UserFilterIn(BaseModel):
    role_id: int | None = None
    department_id: int | None = None
    status: int | None = None
    keyword: str | None = Field(default=None, max_length=64)
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)


class UserBatchImportIn(BaseModel):
    csv_text: str = Field(min_length=1)
    dry_run: bool = False
