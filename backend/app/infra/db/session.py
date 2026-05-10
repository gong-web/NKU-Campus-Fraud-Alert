"""异步 SQLAlchemy session 工厂 + Unit-of-Work。

仅一个 ``async_engine`` 单例；每个请求（或 service 调用）拿一个独立 session，
上下文结束自动 commit / rollback。

服务层（``app.services``）使用方式：

.. code-block:: python

    async with uow() as session:
        repo = UserRepository(session)
        user = await repo.get_by_id(uid)
        # ...

不要在 controller / api 层直接 import 此模块；通过仓储接口访问。
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings

_engine: AsyncEngine | None = None
_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    """获取（或创建）全局 async engine。"""
    global _engine
    if _engine is None:
        s = get_settings().database
        _engine = create_async_engine(
            s.url,
            pool_size=s.pool_size,
            max_overflow=s.max_overflow,
            pool_recycle=s.pool_recycle,
            pool_pre_ping=True,
            echo=s.echo,
            future=True,
        )
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """获取（或创建）session factory。"""
    global _factory
    if _factory is None:
        _factory = async_sessionmaker(
            bind=get_engine(),
            expire_on_commit=False,  # commit 后不丢失对象状态
            autoflush=False,
            class_=AsyncSession,
        )
    return _factory


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency 风格的 session 提供者（自动 rollback）。"""
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


@asynccontextmanager
async def uow() -> AsyncIterator[AsyncSession]:
    """显式 Unit-of-Work：service 层使用。

    成功路径自动 commit；异常自动 rollback。
    """
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def dispose_engine() -> None:
    """关闭 engine（应用退出时调用）。"""
    global _engine, _factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _factory = None
