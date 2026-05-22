"""Mock CAS Provider —— 本地开发体验关键。

行为
----
- ``login_url(service)`` 返回前端 Mock 登录页 URL；前端展示一个 "学号" 输入框。
- 前端把 ``cas_account`` 直接当作 ``ticket`` 传回 ``/auth/cas/callback``，
  本 Provider 接受任意非空字符串视作"登录成功"。
- 返回固定的 ``CASUserInfo``，``real_name`` 取 ``f"测试用户 {cas_account}"``。
- ``healthy()`` 始终返回 True。

为什么这样设计
--------------
- 让 4 个组员在没有学校 CAS 接入的情况下也能完整跑登录、权限、审计的链路；
- 允许测试通过手工修改"票据"模拟各类失败分支（票据为空、过长 → 抛
  ``CASTicketInvalid``）；
- 严格区分于 ``RealCASProvider``，避免 mock 行为污染生产代码。
"""

from __future__ import annotations

from urllib.parse import urlencode, urlsplit

from app.core.config import get_settings
from app.core.logging import get_logger
from app.exceptions import CASTicketInvalid, OpenRedirectBlocked
from app.infra.cas.base import AuthProvider, CASUserInfo

logger = get_logger(__name__)


class MockCASProvider(AuthProvider):
    """本地开发用 CAS Provider。"""

    name = "mock"

    async def validate_ticket(self, ticket: str, *, service: str) -> CASUserInfo:
        if not ticket or not ticket.strip():
            raise CASTicketInvalid("Mock CAS: 票据为空")
        if len(ticket) > 64:
            raise CASTicketInvalid("Mock CAS: 票据过长（疑似异常）")
        # 支持 ``account`` 或 ``account__<nonce>`` 两种形式：
        # - 直接 ``account``：旧的"账号即票据"用法（手填、回归测试）
        # - ``account__<nonce>``：``mock_login`` 端点用，用 nonce 绕过重放保护
        raw = ticket.strip()
        cas_account = raw.split("__", 1)[0]
        if not cas_account:
            raise CASTicketInvalid("Mock CAS: 票据 account 段为空")
        if not raw.isascii() or not raw.replace("_", "").isalnum():
            raise CASTicketInvalid("Mock CAS: 票据格式非法（仅允许 [A-Za-z0-9_]）")
        if not cas_account.replace("_", "").isalnum():
            raise CASTicketInvalid("Mock CAS: account 段格式非法")

        # service 必须在白名单（与 Real 行为一致，给团队留肌肉记忆）
        _ensure_service_whitelisted(service)

        return CASUserInfo(
            cas_account=cas_account,
            real_name=f"测试用户 {cas_account}",
            department_code=None,
            raw_attributes={"provider": "mock"},
        )

    def login_url(self, *, service: str) -> str:
        _ensure_service_whitelisted(service)
        # 直接跳前端的 Mock 登录页（Vite dev 5173 或同源 /auth/mock-login）
        return f"/auth/mock-login?{urlencode({'service': service})}"

    def logout_url(self, *, service: str | None = None) -> str:
        target = service or "/"
        _ensure_service_whitelisted(target)
        return f"/auth/mock-logout?{urlencode({'service': target})}"

    async def healthy(self) -> bool:
        return True


def _ensure_service_whitelisted(service: str) -> None:
    """防开放重定向：service 必须命中预配置 host 白名单。"""
    settings = get_settings()
    whitelist = settings.cas.service_whitelist
    if not whitelist:
        # 未配置白名单时 fallback：仅允许同源；但日志告警
        logger.warning("cas_service_whitelist_empty", service=service)
        return
    host = urlsplit(service).netloc
    allowed_hosts = {urlsplit(a).netloc for a in whitelist}
    if host and host not in allowed_hosts:
        raise OpenRedirectBlocked(f"service={service!r} 不在白名单内")
