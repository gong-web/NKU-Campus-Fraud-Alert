"""Redis 客户端、会话存储、RBAC 缓存。

模块
----
- :mod:`app.infra.cache.client`        — 全局 ``redis.asyncio`` 客户端
- :mod:`app.infra.cache.session_store` — 会话存储（30 分钟滑动过期）
- :mod:`app.infra.cache.rbac_cache`    — RBAC 角色 → 权限码缓存
- :mod:`app.infra.cache.ticket_dedup`  — CAS 票据 5 分钟去重（防重放）
- :mod:`app.infra.cache.audit_stream`  — 审计 Redis Stream 缓冲
"""

from app.infra.cache.client import close_redis, get_redis
from app.infra.cache.rbac_cache import RBACCache
from app.infra.cache.session_store import SessionStore
from app.infra.cache.ticket_dedup import TicketDedup

__all__ = [
    "RBACCache",
    "SessionStore",
    "TicketDedup",
    "close_redis",
    "get_redis",
]
