"""CAS 票据去重（防重放，PRD 第 2.5 章）。"""

from __future__ import annotations

from app.core.config import get_settings
from app.infra.cache.client import get_redis

_DEDUP_TTL_SECONDS = 300  # 5 分钟


class TicketDedup:
    def __init__(self) -> None:
        self._prefix = get_settings().redis.key_prefix
        self._redis = get_redis()

    def _key(self, ticket: str) -> str:
        return f"{self._prefix}:cas_ticket:{ticket}"

    async def acquire(self, ticket: str) -> bool:
        """``True`` 表示首次使用；``False`` 表示重放。"""
        ok = await self._redis.set(self._key(ticket), b"1", ex=_DEDUP_TTL_SECONDS, nx=True)
        return bool(ok)
