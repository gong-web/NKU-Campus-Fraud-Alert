"""RBAC 缓存：``role_id -> {permission_code, ...}``。

启动时把 ``role_permissions`` 全表加载进 Redis hash + set；后续鉴权 O(1)。
任何"角色权限改动"都通过 :meth:`invalidate` 失效缓存 + 通过 Pub/Sub 通知所
有应用实例同步重新加载。

Key 格式
--------
- ``afp:rbac:role:{role_id}``   — set of permission_code
- ``afp:rbac:loaded``           — flag (是否已经从 DB 加载过)
- ``afp:rbac:invalidate``       — pub/sub channel
"""

from __future__ import annotations

from collections.abc import AsyncGenerator, Awaitable
from typing import Any, cast

from app.core.config import get_settings
from app.core.logging import get_logger
from app.infra.cache.client import get_redis

logger = get_logger(__name__)


class RBACCache:
    INVALIDATE_CHANNEL = "afp:rbac:invalidate"

    def __init__(self) -> None:
        s = get_settings()
        self._prefix = s.redis.key_prefix
        self._redis = get_redis()

    def _role_key(self, role_id: int) -> str:
        return f"{self._prefix}:rbac:role:{role_id}"

    @property
    def _loaded_key(self) -> str:
        return f"{self._prefix}:rbac:loaded"

    async def load(self, role_to_perms: dict[int, set[str]]) -> None:
        """全量装载（启动期 / 失效后重建调用）。"""
        pipe = self._redis.pipeline()
        async for key in self._redis.scan_iter(match=f"{self._prefix}:rbac:role:*", count=200):
            pipe.delete(key)
        for role_id, perms in role_to_perms.items():
            if perms:
                pipe.sadd(self._role_key(role_id), *perms)
        pipe.set(self._loaded_key, "1", ex=86_400 * 7)
        await pipe.execute()
        logger.info(
            "rbac_cache_loaded",
            role_count=len(role_to_perms),
            perm_count=sum(len(p) for p in role_to_perms.values()),
        )

    async def has_permission(self, role_id: int, permission_code: str) -> bool:
        """O(1) 查询某角色是否拥有某权限码。"""
        exists = await cast(
            Awaitable[Any],
            self._redis.sismember(self._role_key(role_id), permission_code),
        )
        return bool(exists)

    async def list_permissions(self, role_id: int) -> set[str]:
        members = await cast(Awaitable[set[Any]], self._redis.smembers(self._role_key(role_id)))
        return {m.decode("utf-8") if isinstance(m, (bytes, bytearray)) else m for m in members}

    async def is_loaded(self) -> bool:
        return bool(await self._redis.exists(self._loaded_key))

    async def invalidate(self, *, broadcast: bool = True) -> None:
        """失效本地缓存 + 可选广播。"""
        await self._redis.delete(self._loaded_key)
        if broadcast:
            await self._redis.publish(self.INVALIDATE_CHANNEL, b"reload")
            logger.info("rbac_cache_invalidate_broadcast")

    async def subscribe_invalidate(
        self,
    ) -> AsyncGenerator[bytes, None]:  # pragma: no cover - 启动钩子
        """订阅失效通知（在 lifespan 里启动一个后台 task 调用）。"""
        pubsub = self._redis.pubsub()
        await pubsub.subscribe(self.INVALIDATE_CHANNEL)
        async for msg in pubsub.listen():
            if msg.get("type") == "message":
                yield msg["data"]
