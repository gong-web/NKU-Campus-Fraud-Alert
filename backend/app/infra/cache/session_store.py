"""Redis 会话存储（PRD 第 2.3 章）。

特性
----
- session_id 是 :func:`generate_session_id` 生成的 UUIDv4。
- 数据落 Redis hash：``session:{session_id}``。
- TTL = 30 分钟滑动过期；每次有效请求 :meth:`touch` 续期。
- 强制登出能力：:meth:`revoke`。
- 多端策略：同一用户多 session 列在 ``user_sessions:{user_id}`` set 内，便于
  "踢全部" 与 "高敏角色单端互踢"。

Key 格式
--------
- ``afp:session:{session_id}``           hash {user_id, role_id, dept_id, ...}
- ``afp:user_sessions:{user_id}``        set of session_id
"""

from __future__ import annotations

import json
from collections.abc import Awaitable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, cast

from app.core.config import get_settings
from app.core.security import generate_session_id
from app.infra.cache.client import get_redis


@dataclass
class SessionData:
    """会话内含字段（PRD 第 2.3 章）。"""

    session_id: str
    user_id: int
    role_id: int
    role_code: str
    dept_id: int
    cas_account: str
    real_name: str
    cas_ticket: str | None
    source_ip: str
    user_agent: str
    created_at: datetime
    last_active_at: datetime
    expires_at: datetime

    def to_redis_value(self) -> str:
        d = asdict(self)
        d["created_at"] = self.created_at.isoformat()
        d["last_active_at"] = self.last_active_at.isoformat()
        d["expires_at"] = self.expires_at.isoformat()
        return json.dumps(d, ensure_ascii=False)

    @staticmethod
    def from_redis_value(raw: str | bytes) -> SessionData:
        s = raw.decode("utf-8") if isinstance(raw, (bytes, bytearray)) else raw
        d: dict[str, Any] = json.loads(s)
        return SessionData(
            session_id=d["session_id"],
            user_id=int(d["user_id"]),
            role_id=int(d["role_id"]),
            role_code=d["role_code"],
            dept_id=int(d["dept_id"]),
            cas_account=d["cas_account"],
            real_name=d["real_name"],
            cas_ticket=d.get("cas_ticket"),
            source_ip=d["source_ip"],
            user_agent=d["user_agent"],
            created_at=datetime.fromisoformat(d["created_at"]),
            last_active_at=datetime.fromisoformat(d["last_active_at"]),
            expires_at=datetime.fromisoformat(d["expires_at"]),
        )


class SessionStore:
    """会话存储（async）。"""

    HIGH_PRIVILEGE_ROLES = frozenset({"SYS_ADMIN"})

    def __init__(self) -> None:
        s = get_settings()
        self._ttl = s.security.session_ttl_seconds
        self._prefix = s.redis.key_prefix
        self._redis = get_redis()

    # ── key 工具 ─────────────────────────────────────────────
    def _session_key(self, sid: str) -> str:
        return f"{self._prefix}:session:{sid}"

    def _user_sessions_key(self, uid: int) -> str:
        return f"{self._prefix}:user_sessions:{uid}"

    # ── 写 ────────────────────────────────────────────────────
    async def create(
        self,
        *,
        user_id: int,
        role_id: int,
        role_code: str,
        dept_id: int,
        cas_account: str,
        real_name: str,
        cas_ticket: str | None,
        source_ip: str,
        user_agent: str,
    ) -> SessionData:
        """创建一个新 session（登录成功后调用）。"""
        # 高敏角色：单端互踢——撤销该用户所有旧 session
        if role_code in self.HIGH_PRIVILEGE_ROLES:
            await self.revoke_all_for_user(user_id)

        now = datetime.now(tz=UTC)
        session = SessionData(
            session_id=generate_session_id(),
            user_id=user_id,
            role_id=role_id,
            role_code=role_code,
            dept_id=dept_id,
            cas_account=cas_account,
            real_name=real_name,
            cas_ticket=cas_ticket,
            source_ip=source_ip,
            user_agent=user_agent,
            created_at=now,
            last_active_at=now,
            expires_at=now + timedelta(seconds=self._ttl),
        )
        pipe = self._redis.pipeline()
        pipe.set(self._session_key(session.session_id), session.to_redis_value(), ex=self._ttl)
        pipe.sadd(self._user_sessions_key(user_id), session.session_id)
        pipe.expire(self._user_sessions_key(user_id), self._ttl * 4)
        await pipe.execute()
        return session

    async def touch(self, sid: str) -> SessionData | None:
        """续期：更新 last_active_at + 重置 TTL。"""
        raw = await self._redis.get(self._session_key(sid))
        if raw is None:
            return None
        session = SessionData.from_redis_value(raw)
        now = datetime.now(tz=UTC)
        session.last_active_at = now
        session.expires_at = now + timedelta(seconds=self._ttl)
        await self._redis.set(self._session_key(sid), session.to_redis_value(), ex=self._ttl)
        return session

    # ── 读 ────────────────────────────────────────────────────
    async def get(self, sid: str) -> SessionData | None:
        raw = await self._redis.get(self._session_key(sid))
        if raw is None:
            return None
        return SessionData.from_redis_value(raw)

    # ── 撤销 ──────────────────────────────────────────────────
    async def revoke(self, sid: str) -> bool:
        """主动登出 / 强制踢人。返回是否实际删了一条。"""
        session = await self.get(sid)
        if session is None:
            return False
        pipe = self._redis.pipeline()
        pipe.delete(self._session_key(sid))
        pipe.srem(self._user_sessions_key(session.user_id), sid)
        await pipe.execute()
        return True

    async def revoke_all_for_user(self, user_id: int) -> int:
        """撤销某用户所有 session（角色变更 / 停用 / 高敏单端登录时调用）。"""
        sids = await cast(
            Awaitable[set[Any]],
            self._redis.smembers(self._user_sessions_key(user_id)),
        )
        if not sids:
            return 0
        pipe = self._redis.pipeline()
        for sid in sids:
            sid_str = sid.decode() if isinstance(sid, (bytes, bytearray)) else sid
            pipe.delete(self._session_key(sid_str))
        pipe.delete(self._user_sessions_key(user_id))
        await pipe.execute()
        return len(sids)

    async def active_count_by_role(self) -> dict[str, int]:
        """供 Prometheus exporter 调用：``active_sessions_total{role=...}``。

        实现上扫描所有 ``afp:session:*``，量大时用 SCAN（cursor）而非 KEYS。
        """
        counts: dict[str, int] = {}
        async for key in self._redis.scan_iter(match=f"{self._prefix}:session:*", count=200):
            raw = await self._redis.get(key)
            if raw is None:
                continue
            try:
                session = SessionData.from_redis_value(raw)
            except (ValueError, KeyError):
                continue
            counts[session.role_code] = counts.get(session.role_code, 0) + 1
        return counts
