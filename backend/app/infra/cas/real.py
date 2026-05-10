"""Real CAS Provider —— 对接学校 CAS 3.0。

协议要点
--------
- ``GET <server>/login?service=<callback>`` 重定向用户输入账号密码。
- CAS 校验通过后回跳 ``<callback>?ticket=ST-...``。
- 后端 ``GET <server>/p3/serviceValidate?service=<callback>&ticket=<ST>``
  得到 XML，里面 ``<cas:authenticationSuccess>`` 即认证成功。
- 一次性消费：同一 ticket 不能用两次（CAS 服务器侧拒绝；本地我们也 5 分钟
  Redis 去重，防御重放）。
- 安全：``service`` 必须命中白名单；XML 必须用 ``defusedxml`` 防 XXE。

错误分类（PRD 第 2.2 章 + 2.5 章）：

- 网络超时 / 连接失败 → :class:`CASUnreachable`
- 票据格式异常 / 校验返回 ``authenticationFailure`` → :class:`CASTicketInvalid`
- 票据已被使用（5 分钟去重命中）→ :class:`CASTicketReplay`
"""

from __future__ import annotations

from urllib.parse import urlencode, urlsplit

import httpx
from defusedxml import ElementTree as ET
from defusedxml.common import DefusedXmlException

from app.core.config import get_settings
from app.core.logging import get_logger
from app.exceptions import (
    CASTicketInvalid,
    CASUnreachable,
    OpenRedirectBlocked,
)
from app.infra.cas.base import AuthProvider, CASUserInfo

logger = get_logger(__name__)

_CAS_NS = {"cas": "http://www.yale.edu/tp/cas"}


class RealCASProvider(AuthProvider):
    """对接学校 CAS 3.0。"""

    name = "real"

    def __init__(self) -> None:
        cas = get_settings().cas
        self._server = cas.server_url.rstrip("/")
        self._timeout = cas.timeout_seconds

    async def validate_ticket(self, ticket: str, *, service: str) -> CASUserInfo:
        if not ticket or not ticket.startswith(("ST-", "PT-")):
            raise CASTicketInvalid("CAS 票据格式非法")
        _ensure_service_whitelisted(service)

        url = f"{self._server}/p3/serviceValidate"
        params = {"service": service, "ticket": ticket, "format": "XML"}

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.get(url, params=params)
        except httpx.HTTPError as exc:
            logger.warning("cas_unreachable", reason=str(exc), url=url)
            raise CASUnreachable() from exc

        if resp.status_code != 200:
            raise CASTicketInvalid(f"CAS serviceValidate HTTP {resp.status_code}")

        return _parse_validate_xml(resp.text)

    def login_url(self, *, service: str) -> str:
        _ensure_service_whitelisted(service)
        return f"{self._server}/login?{urlencode({'service': service})}"

    def logout_url(self, *, service: str | None = None) -> str:
        if service:
            _ensure_service_whitelisted(service)
            return f"{self._server}/logout?{urlencode({'service': service})}"
        return f"{self._server}/logout"

    async def healthy(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.get(f"{self._server}/login")
                return resp.status_code in (200, 302)
        except httpx.HTTPError:
            return False


# ── 解析 ───────────────────────────────────────────────────────────
def _parse_validate_xml(xml_text: str) -> CASUserInfo:
    """解析 ``serviceValidate`` 的 XML（XXE-safe）。"""
    try:
        root = ET.fromstring(xml_text)
    except (ET.ParseError, DefusedXmlException) as exc:
        # XXE / DTD / 外部实体 都视为非法票据
        raise CASTicketInvalid("CAS 返回 XML 解析失败（可能含外部实体）") from exc

    success = root.find("cas:authenticationSuccess", _CAS_NS)
    if success is None:
        # authenticationFailure 分支
        failure = root.find("cas:authenticationFailure", _CAS_NS)
        reason = failure.text.strip() if failure is not None and failure.text else "Unknown"
        raise CASTicketInvalid(f"CAS authenticationFailure: {reason}")

    user_node = success.find("cas:user", _CAS_NS)
    if user_node is None or not (user_node.text or "").strip():
        raise CASTicketInvalid("CAS 返回缺少 <cas:user>")
    cas_account = user_node.text.strip()

    attrs_node = success.find("cas:attributes", _CAS_NS)
    raw: dict[str, str] = {}
    if attrs_node is not None:
        for child in attrs_node:
            tag = child.tag.split("}", 1)[-1]  # 去掉命名空间
            raw[tag] = (child.text or "").strip()

    return CASUserInfo(
        cas_account=cas_account,
        real_name=raw.get("name") or raw.get("realName") or cas_account,
        department_code=raw.get("departmentCode") or raw.get("dept"),
        raw_attributes=raw or None,
    )


def _ensure_service_whitelisted(service: str) -> None:
    """防开放重定向漏洞。"""
    settings = get_settings()
    whitelist = settings.cas.service_whitelist
    if not whitelist:
        # 生产环境无白名单视为配置错误（在 config 里已做校验，这里兜底）
        if settings.app_env == "prod":
            raise OpenRedirectBlocked("生产环境必须配置 CAS_SERVICE_WHITELIST")
        return
    host = urlsplit(service).netloc
    allowed_hosts = {urlsplit(a).netloc for a in whitelist}
    if host and host not in allowed_hosts:
        raise OpenRedirectBlocked(f"service={service!r} 不在白名单内")
