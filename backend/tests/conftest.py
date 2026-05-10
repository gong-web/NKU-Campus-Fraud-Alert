"""共享测试 fixtures。

约定
----
- ``client`` —— httpx ``AsyncClient``，会自动带 CSRF header。
- ``mock_cas_provider`` —— 永远 mock，组员单测无须真 CAS。
- ``authenticated_client(role)`` —— 给定角色的预登录客户端。
- ``db_session`` —— 每个用例独立事务并自动回滚。
- ``fakeredis`` —— 取代真实 Redis（可在单元测试里用）。
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator, Callable
from contextlib import suppress
from typing import Any

import fakeredis.aioredis
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine

# 测试环境变量必须在导入 app.* 之前设置！
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("AUTH_PROVIDER", "mock")
os.environ.setdefault("SECRET_KEY", "test-secret-key-with-at-least-16-bytes!")
os.environ.setdefault("KMS_PROVIDER", "local")
os.environ.setdefault(
    "KMS_LOCAL_MASTER_KEY",
    "dGVzdC1tYXN0ZXIta2V5LWZvci1jaS1vbmx5LTMyLWJ5dGVzIQ==",
)
# 默认用 sqlite+aiosqlite 让单元测试无需真 MySQL；集成测试会 override
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:?cache=shared")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/15")
os.environ.setdefault("OPENAPI_ENABLED", "true")
os.environ.setdefault("CAS_SERVICE_WHITELIST", "")
os.environ.setdefault("MOCK_CAS_ALLOW_ANY", "true")
os.environ.setdefault("PROMETHEUS_ENABLED", "false")
os.environ.setdefault("AUDIT_FALLBACK_PATH", "/tmp/audit_fallback.jsonl")
os.environ.setdefault("CORS_ALLOW_ORIGINS", "http://test")


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
async def fake_redis() -> AsyncIterator[fakeredis.aioredis.FakeRedis]:
    """fakeredis 替代真 Redis（单元测试默认）。"""
    r = fakeredis.aioredis.FakeRedis()
    yield r
    await r.aclose()


@pytest.fixture(autouse=True)
def patch_redis_client(
    monkeypatch: pytest.MonkeyPatch, fake_redis: fakeredis.aioredis.FakeRedis
) -> None:
    """把 ``app.infra.cache.client.get_redis`` 重定向到 fakeredis。"""
    from app.infra.cache import client as client_mod

    monkeypatch.setattr(client_mod, "_redis", fake_redis, raising=False)
    monkeypatch.setattr(client_mod, "get_redis", lambda: fake_redis)

    # 同步 import 链中其它 module 已经 cache 的 get_redis
    import importlib

    for name in [
        "app.infra.cache.session_store",
        "app.infra.cache.rbac_cache",
        "app.infra.cache.ticket_dedup",
        "app.infra.cache.audit_stream",
    ]:
        with suppress(ImportError):
            importlib.import_module(name)


@pytest.fixture
async def db_engine() -> AsyncIterator[AsyncEngine]:
    """SQLite in-memory engine + 建表（单元/集成默认用）。"""
    from app.infra.db.base import Base

    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:?cache=shared",
        connect_args={"check_same_thread": False},
        future=True,
    )
    # 注意：模型里 VARBINARY / JSON 在 sqlite 下会落到 LargeBinary / JSON 兼容。
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def db_session(
    db_engine: AsyncEngine, monkeypatch: pytest.MonkeyPatch
) -> AsyncIterator[AsyncSession]:
    """每用例独立事务 + 回滚（避免污染）。"""
    from app.infra.db import session as db_session_mod

    monkeypatch.setattr(db_session_mod, "_engine", db_engine)
    factory = db_session_mod.async_sessionmaker(
        bind=db_engine, expire_on_commit=False, autoflush=False, class_=AsyncSession
    )
    monkeypatch.setattr(db_session_mod, "_factory", factory)

    async with factory() as session:
        yield session
        # session-level rollback；测试不允许污染数据
        await session.rollback()


@pytest.fixture
async def client(db_engine: AsyncEngine) -> AsyncIterator[AsyncClient]:
    """httpx ASGI client，自动带 CSRF header。"""
    del db_engine  # only ensure engine is initialized
    from app.main import create_app

    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={"X-Requested-With": "XMLHttpRequest"},
    ) as c:
        yield c


@pytest.fixture
async def authenticated_client(client: AsyncClient) -> Callable[[str], Any]:
    """给定 cas_account 即返回一个已登录的 client。"""

    async def _login(cas_account: str = "student001") -> AsyncClient:
        resp = await client.post(
            "/api/v1/auth/cas/mock-login",
            json={"cas_account": cas_account},
        )
        assert resp.status_code == 200, resp.text
        return client

    return _login
