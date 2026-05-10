"""5 分钟冒烟（地基组负责的部分）。

完整业务（上报 / 审核 / 预警 / 答题）的冒烟由各 UC 模块负责人在自己的
PR 中追加。
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.e2e


@pytest.mark.asyncio
async def test_health(client: AsyncClient) -> None:
    resp = await client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_openapi_available(client: AsyncClient) -> None:
    resp = await client.get("/openapi.json")
    assert resp.status_code == 200
    paths = resp.json()["paths"]
    # 关键路径都应已注册
    for p in [
        "/api/v1/auth/cas/login-url",
        "/api/v1/auth/cas/mock-login",
        "/api/v1/auth/me",
        "/api/v1/auth/logout",
        "/api/v1/users",
        "/api/v1/audit-logs",
        "/api/v1/judicial-assist/request-decryption",
    ]:
        assert p in paths, f"missing: {p}"
