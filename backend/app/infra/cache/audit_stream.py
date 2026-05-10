"""审计日志 Redis Stream 缓冲。

主请求路径只把"待写入的审计 JSON"扔进 Stream（O(1)），后台 worker 批量消费
落库；如果 Stream 也挂了，调用方会感知并 fallback 到本地 jsonl 文件。

强一致场景（登录、权限变更、解密匿名）由 audit_service 直接同步落库，**不**
经过本通道。
"""

from __future__ import annotations

import json
from typing import Any

from app.core.config import get_settings
from app.infra.cache.client import get_redis


class AuditStream:
    def __init__(self) -> None:
        s = get_settings().redis
        self._stream_key = s.audit_stream_key
        self._maxlen = s.audit_stream_maxlen
        self._redis = get_redis()

    async def push(self, payload: dict[str, Any]) -> str:
        """放入一条待落库的审计 payload；返回 Stream message id。"""
        body = json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")
        msg_id = await self._redis.xadd(
            self._stream_key,
            {b"payload": body},
            maxlen=self._maxlen,
            approximate=True,
        )
        return msg_id.decode("utf-8") if isinstance(msg_id, (bytes, bytearray)) else msg_id

    async def pop_batch(self, count: int = 100, block_ms: int = 1000) -> list[dict[str, Any]]:
        """worker 调用：拉一批 payload。

        本骨架未提供 consumer group 实现，留给运维以后接 ``XREADGROUP``。
        """
        result = await self._redis.xread({self._stream_key: "$"}, count=count, block=block_ms)
        out: list[dict[str, Any]] = []
        for _, messages in result or []:
            for _, fields in messages:
                raw = fields.get(b"payload")
                if raw is None:
                    continue
                out.append(json.loads(raw))
        return out
