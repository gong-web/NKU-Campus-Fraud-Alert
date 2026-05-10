"""FastAPI 依赖注入：鉴权与权限校验。

给团队 4 人用的核心 API
-----------------------
所有写接口必须用以下三种之一注入"当前用户 + 鉴权"，**禁止**在 controller
里写 ``if user.role == 'reviewer'`` 这种 ad-hoc 判断（违反者 PR 直接打回）。

::

    # 任何登录用户
    current: UserSnapshot = Depends(get_current_user)

    # 角色限定（白名单）
    current = Depends(require_role("Reviewer", "SysAdmin"))

    # 细粒度权限码
    current = Depends(require_permission("user:create"))

    # "本人 or 管理员"语义
    current = Depends(require_self_or_role("user_id", "SysAdmin"))

每个依赖都返回不可变的 :class:`UserSnapshot`，下游 service 拿到的是只读
身份名片，不会出现"协程跨函数共享 ORM 对象"的坑。
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Iterable
from typing import Annotated

from fastapi import Cookie, Depends, Request

from app.core.config import get_settings
from app.core.logging import bind_request_context, get_logger
from app.domain.user_snapshot import UserSnapshot
from app.exceptions import PermissionDenied, Unauthenticated
from app.infra.cache.rbac_cache import RBACCache
from app.infra.cache.session_store import SessionStore

logger = get_logger(__name__)


# ── 基础：取 session id ──────────────────────────────────────
def _session_cookie_name() -> str:
    return get_settings().security.session_cookie_name


# ── 1. 任何登录用户 ─────────────────────────────────────────────
async def get_current_user(
    request: Request,
    afp_session: Annotated[
        str | None,
        Cookie(
            alias=None,  # 实际名由 settings 决定（FastAPI Cookie alias 不能动态注入）
            description="会话 Cookie",
        ),
    ] = None,
) -> UserSnapshot:
    """从 cookie 取 session_id；查 Redis；返回 UserSnapshot。

    任意环节失败抛 :class:`Unauthenticated`。
    """
    # 兼容动态 cookie 名：直接从 request.cookies 取
    cookie_name = _session_cookie_name()
    sid = request.cookies.get(cookie_name) or afp_session
    if not sid:
        raise Unauthenticated("缺少会话 Cookie")

    store = SessionStore()
    sd = await store.touch(sid)
    if sd is None:
        raise Unauthenticated("会话不存在或已过期")

    snap = UserSnapshot(
        user_id=sd.user_id,
        cas_account=sd.cas_account,
        real_name=sd.real_name,
        role_id=sd.role_id,
        role_code=sd.role_code,
        department_id=sd.dept_id,
        session_id=sd.session_id,
        source_ip=request.client.host if request.client else "",
        user_agent=request.headers.get("user-agent", "") or "",
    )
    bind_request_context(
        trace_id=getattr(request.state, "trace_id", None),
        user_id=snap.user_id,
        source_ip=snap.source_ip,
    )
    return snap


# ── 2. 角色限定 ────────────────────────────────────────────────
def require_role(*allowed_roles: str) -> Callable[..., Awaitable[UserSnapshot]]:
    """生成一个 dependency：要求当前用户角色在 ``allowed_roles`` 内。"""
    allowed = _normalize(allowed_roles)

    async def _dep(current: Annotated[UserSnapshot, Depends(get_current_user)]) -> UserSnapshot:
        if current.role_code not in allowed:
            logger.warning(
                "rbac_role_denied",
                user_id=current.user_id,
                role=current.role_code,
                required=sorted(allowed),
            )
            raise PermissionDenied(f"需要角色 {sorted(allowed)}")
        return current

    _dep.__name__ = f"require_role[{','.join(sorted(allowed))}]"
    return _dep


# ── 3. 权限码 ──────────────────────────────────────────────────
def require_permission(perm_code: str) -> Callable[..., Awaitable[UserSnapshot]]:
    """生成一个 dependency：要求当前用户角色拥有 ``perm_code``。"""
    if not perm_code or ":" not in perm_code:
        raise ValueError(f"非法权限码: {perm_code!r}")

    async def _dep(current: Annotated[UserSnapshot, Depends(get_current_user)]) -> UserSnapshot:
        rbac = RBACCache()
        if await rbac.has_permission(current.role_id, perm_code):
            return current
        logger.warning(
            "rbac_perm_denied",
            user_id=current.user_id,
            role_id=current.role_id,
            required=perm_code,
        )
        raise PermissionDenied(f"权限不足，需要 {perm_code}")

    _dep.__name__ = f"require_permission[{perm_code}]"
    return _dep


# ── 4. "自己 or 角色" ──────────────────────────────────────────
def require_self_or_role(
    target_user_id_arg: str, *allowed_roles: str
) -> Callable[..., Awaitable[UserSnapshot]]:
    """如果路径参数 ``target_user_id_arg`` 等于当前 user_id 即放行；否则要求角色。"""
    allowed = _normalize(allowed_roles)

    async def _dep(
        request: Request,
        current: Annotated[UserSnapshot, Depends(get_current_user)],
    ) -> UserSnapshot:
        target = request.path_params.get(target_user_id_arg)
        if target is not None:
            try:
                target_int = int(target)
            except (TypeError, ValueError):
                target_int = -1
            if target_int == current.user_id:
                return current
        if current.role_code in allowed:
            return current
        logger.warning(
            "rbac_self_or_role_denied",
            user_id=current.user_id,
            target=target,
            required=sorted(allowed),
        )
        raise PermissionDenied("需要本人或管理员")

    _dep.__name__ = f"require_self_or_role[{target_user_id_arg},{','.join(sorted(allowed))}]"
    return _dep


def _normalize(roles: Iterable[str]) -> frozenset[str]:
    """统一规范化角色码：``Student`` / ``student`` / ``STUDENT`` 都接受。

    内部存储与比较仍用大写。
    """
    out: set[str] = set()
    aliases = {
        "STUDENT": "STUDENT",
        "REVIEWER": "REVIEWER",
        "SYSADMIN": "SYS_ADMIN",
        "SYS_ADMIN": "SYS_ADMIN",
        "ADMIN": "SYS_ADMIN",
    }
    for r in roles:
        up = r.upper().replace("-", "_")
        if up not in aliases:
            raise ValueError(f"未知角色 {r!r}")
        out.add(aliases[up])
    return frozenset(out)
