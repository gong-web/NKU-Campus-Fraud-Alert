"""鉴权接口（UC-00 CAS 单点登录）。

接口
----
- ``GET  /api/v1/auth/cas/login-url``  — 生成 CAS 登录 URL
- ``GET  /api/v1/auth/cas/callback``   — CAS 回调（带 ticket + service）
- ``POST /api/v1/auth/cas/mock-login`` — 仅 Mock 模式可用
- ``GET  /api/v1/auth/me``             — 当前用户信息（含权限码集合）
- ``POST /api/v1/auth/logout``         — 登出
"""

from __future__ import annotations

from typing import Annotated
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Query, Request, Response, status
from fastapi.responses import RedirectResponse

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.logging import get_logger
from app.domain.user_snapshot import UserSnapshot
from app.exceptions import OpenRedirectBlocked
from app.infra.cache.rbac_cache import RBACCache
from app.infra.cas.factory import get_auth_provider
from app.schemas.auth import LoginUrlOut, LogoutOut, MockLoginIn, WhoAmIOut
from app.services.auth_service import AuthService

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["auth (UC-00)"])


# ── login-url ────────────────────────────────────────────────────
@router.get(
    "/cas/login-url",
    response_model=LoginUrlOut,
    summary="生成 CAS 登录 URL（前端跳转用）",
)
async def get_cas_login_url(
    service: Annotated[str | None, Query(description="回跳地址；缺省取配置")] = None,
) -> LoginUrlOut:
    settings = get_settings()
    target = service or settings.cas.service_url
    provider = get_auth_provider()
    return LoginUrlOut(
        login_url=provider.login_url(service=target),
        provider=provider.name,
        healthy=await provider.healthy(),
    )


# ── CAS 回调 ─────────────────────────────────────────────────────
@router.get(
    "/cas/callback",
    summary="CAS 回调：消费 ticket、建立 session 并跳转工作台",
    status_code=status.HTTP_302_FOUND,
)
async def cas_callback(
    request: Request,
    ticket: Annotated[str, Query(min_length=1, max_length=128)],
    service: Annotated[str, Query(min_length=1, max_length=512)],
) -> RedirectResponse:
    settings = get_settings()
    # 白名单校验：service 必须在配置内（防开放重定向）
    whitelist = settings.cas.service_whitelist or []
    if whitelist:
        from urllib.parse import urlsplit

        host = urlsplit(service).netloc
        allowed_hosts = {urlsplit(a).netloc for a in whitelist}
        if host and host not in allowed_hosts:
            raise OpenRedirectBlocked(f"service={service!r} 不在白名单内")

    provider = get_auth_provider()
    auth_svc = AuthService(provider=provider)
    sd, snap = await auth_svc.cas_login(
        ticket=ticket,
        service=service,
        source_ip=request.client.host if request.client else "",
        user_agent=request.headers.get("user-agent", "") or "",
    )
    response = _redirect_for_role(snap.role_code)
    _set_session_cookie(response, sd.session_id)
    logger.info("cas_callback_ok", user_id=snap.user_id, role=snap.role_code)
    return response


# ── Mock CAS 登录（仅开发用） ─────────────────────────────────────
@router.post(
    "/cas/mock-login",
    summary="Mock CAS 登录（生产环境禁用）",
    response_model=WhoAmIOut,
)
async def mock_login(
    request: Request,
    body: MockLoginIn,
    response: Response,
) -> WhoAmIOut:
    settings = get_settings()
    if settings.auth_provider != "mock":
        raise OpenRedirectBlocked("当前 AUTH_PROVIDER != mock，本接口被禁用")

    provider = get_auth_provider()
    auth_svc = AuthService(provider=provider)
    sd, snap = await auth_svc.cas_login(
        ticket=body.cas_account,  # mock 模式：cas_account 即票据
        service=body.service or settings.cas.service_url,
        source_ip=request.client.host if request.client else "",
        user_agent=request.headers.get("user-agent", "") or "",
    )
    _set_session_cookie(response, sd.session_id)
    rbac = RBACCache()
    perms = await rbac.list_permissions(snap.role_id)
    return WhoAmIOut(
        user_id=snap.user_id,
        cas_account=snap.cas_account,
        real_name=snap.real_name,
        role_id=snap.role_id,
        role_code=snap.role_code,
        department_id=snap.department_id,
        permissions=sorted(perms),
        session_expires_in_seconds=settings.security.session_ttl_seconds,
    )


# ── /me ──────────────────────────────────────────────────────────
@router.get(
    "/me",
    response_model=WhoAmIOut,
    summary="当前用户信息",
)
async def whoami(
    current: Annotated[UserSnapshot, Depends(get_current_user)],
) -> WhoAmIOut:
    rbac = RBACCache()
    perms = await rbac.list_permissions(current.role_id)
    auth_svc = AuthService(provider=get_auth_provider())
    return WhoAmIOut(
        user_id=current.user_id,
        cas_account=current.cas_account,
        real_name=current.real_name,
        role_id=current.role_id,
        role_code=current.role_code,
        department_id=current.department_id,
        permissions=sorted(perms),
        session_expires_in_seconds=await auth_svc.remaining_seconds(current.session_id),
    )


# ── 登出 ─────────────────────────────────────────────────────────
@router.post(
    "/logout",
    response_model=LogoutOut,
    summary="登出（清除本地会话 + 返回 CAS logout URL）",
)
async def logout(
    response: Response,
    current: Annotated[UserSnapshot, Depends(get_current_user)],
) -> LogoutOut:
    auth_svc = AuthService(provider=get_auth_provider())
    cas_logout = await auth_svc.logout(current)
    _clear_session_cookie(response)
    return LogoutOut(cas_logout_url=cas_logout)


# ── 工具 ──────────────────────────────────────────────────────────
def _set_session_cookie(response: Response, sid: str) -> None:
    s = get_settings().security
    response.set_cookie(
        key=s.session_cookie_name,
        value=sid,
        max_age=s.session_ttl_seconds,
        httponly=True,
        secure=s.session_cookie_secure,
        samesite=s.session_cookie_samesite,
        domain=s.session_cookie_domain or None,
        path="/",
    )


def _clear_session_cookie(response: Response) -> None:
    s = get_settings().security
    response.delete_cookie(
        key=s.session_cookie_name,
        domain=s.session_cookie_domain or None,
        path="/",
    )


def _redirect_for_role(role_code: str) -> RedirectResponse:
    """登录成功后按角色跳前端工作台（PRD 2.6）。"""
    target = {
        "STUDENT": "/student/home",
        "REVIEWER": "/admin/dashboard",
        "SYS_ADMIN": "/sys/dashboard",
    }.get(role_code, "/")
    return RedirectResponse(url=target, status_code=status.HTTP_302_FOUND)


# 让旧 url 兼容（FastAPI urlencode 工具就是为了避免遗漏，未来 PR 加）
__all__ = ["_set_session_cookie", "router"]
_ = urlencode  # 引用以避免 unused
