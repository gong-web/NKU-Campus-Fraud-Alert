"""鉴权相关 schemas。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class CASCallbackQuery(BaseModel):
    """CAS 回调 query string。"""

    ticket: str = Field(min_length=1, max_length=128)
    service: str = Field(min_length=1, max_length=512)


class LoginUrlOut(BaseModel):
    """``GET /api/v1/auth/cas/login-url`` 响应。"""

    login_url: str
    provider: str
    healthy: bool


class WhoAmIOut(BaseModel):
    """``GET /api/v1/auth/me`` 响应。"""

    user_id: int
    cas_account: str
    real_name: str
    role_id: int
    role_code: str
    department_id: int
    permissions: list[str]
    session_expires_in_seconds: int


class LogoutOut(BaseModel):
    cas_logout_url: str


class MockLoginIn(BaseModel):
    """Mock CAS 用：直接传 cas_account 完成登录。"""

    cas_account: str = Field(min_length=1, max_length=32)
    service: str | None = Field(default=None, max_length=512)
