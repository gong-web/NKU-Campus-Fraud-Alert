"""CAS Provider 单元测试（4 类典型攻击）。"""

from __future__ import annotations

import os

import pytest

from app.exceptions import CASTicketInvalid, OpenRedirectBlocked
from app.infra.cas.mock import MockCASProvider


@pytest.mark.asyncio
class TestMockProviderAttacks:
    """PRD 第 2.7 章 自检 4 类攻击的 mock 模式覆盖。"""

    async def test_empty_ticket(self) -> None:
        p = MockCASProvider()
        with pytest.raises(CASTicketInvalid):
            await p.validate_ticket("", service="http://localhost:8000/cb")

    async def test_oversized_ticket(self) -> None:
        p = MockCASProvider()
        with pytest.raises(CASTicketInvalid):
            await p.validate_ticket("x" * 100, service="http://localhost:8000/cb")

    async def test_bad_chars(self) -> None:
        p = MockCASProvider()
        with pytest.raises(CASTicketInvalid):
            await p.validate_ticket("a; DROP TABLE users", service="http://localhost:8000/cb")

    async def test_open_redirect_blocked(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # 配置白名单后，任意非白名单 host 都应被拒
        monkeypatch.setenv(
            "CAS_SERVICE_WHITELIST",
            "http://localhost:8000/cb,http://localhost:5173/cb",
        )
        # 重新加载 settings cache
        from app.core.config import get_settings

        get_settings.cache_clear()  # type: ignore[attr-defined]
        try:
            p = MockCASProvider()
            with pytest.raises(OpenRedirectBlocked):
                await p.validate_ticket("alice", service="https://evil.com/steal")
        finally:
            os.environ["CAS_SERVICE_WHITELIST"] = ""
            get_settings.cache_clear()  # type: ignore[attr-defined]


@pytest.mark.asyncio
class TestRealProviderXmlParse:
    """Real CAS XML 解析（不打真请求，只测纯解析）。"""

    async def test_authentication_success(self) -> None:
        from app.infra.cas.real import _parse_validate_xml

        xml = """<?xml version="1.0" encoding="UTF-8"?>
            <cas:serviceResponse xmlns:cas="http://www.yale.edu/tp/cas">
              <cas:authenticationSuccess>
                <cas:user>2312345</cas:user>
                <cas:attributes>
                  <cas:name>张三</cas:name>
                  <cas:departmentCode>CS</cas:departmentCode>
                </cas:attributes>
              </cas:authenticationSuccess>
            </cas:serviceResponse>"""
        info = _parse_validate_xml(xml)
        assert info.cas_account == "2312345"
        assert info.real_name == "张三"
        assert info.department_code == "CS"

    async def test_authentication_failure(self) -> None:
        from app.infra.cas.real import _parse_validate_xml

        xml = """<?xml version="1.0" encoding="UTF-8"?>
            <cas:serviceResponse xmlns:cas="http://www.yale.edu/tp/cas">
              <cas:authenticationFailure code="INVALID_TICKET">Bad</cas:authenticationFailure>
            </cas:serviceResponse>"""
        with pytest.raises(CASTicketInvalid):
            _parse_validate_xml(xml)

    async def test_xxe_safe(self) -> None:
        """defusedxml 应阻止外部实体解析。"""
        from app.infra.cas.real import _parse_validate_xml

        xml = (
            '<?xml version="1.0"?>'
            '<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>'
            '<cas:serviceResponse xmlns:cas="http://www.yale.edu/tp/cas">'
            "<cas:authenticationSuccess>"
            "<cas:user>&xxe;</cas:user>"
            "</cas:authenticationSuccess>"
            "</cas:serviceResponse>"
        )
        with pytest.raises(CASTicketInvalid):
            _parse_validate_xml(xml)
