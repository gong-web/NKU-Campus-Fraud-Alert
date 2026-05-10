"""全局 ``redis.asyncio`` 客户端单例。"""

from __future__ import annotations

from typing import cast

from redis.asyncio import Redis, from_url

from app.core.config import get_settings

_redis: Redis | None = None


def get_redis() -> Redis:
    """获取全局 Redis 客户端（async）。"""
    global _redis
    if _redis is None:
        url = get_settings().redis.url
        _redis = cast(
            Redis,
            from_url(  # type: ignore[no-untyped-call]
                url,
                encoding="utf-8",
                decode_responses=False,
                health_check_interval=30,
            ),
        )
    return _redis


async def close_redis() -> None:
    """关闭客户端（应用退出时调用）。"""
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None
