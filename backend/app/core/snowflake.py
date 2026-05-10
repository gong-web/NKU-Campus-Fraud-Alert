"""雪花 ID 生成器。

基于 Twitter Snowflake 的 64 位整数 ID：

::

    1 bit (符号位) | 41 bit 时间戳 (ms) | 5 bit datacenter | 5 bit worker | 12 bit 序列

时间起点（epoch）通过配置注入，默认 ``2025-01-01 00:00:00 UTC``，可保证
约 69 年内 ID 单调递增。同一毫秒内同一 worker 最多 4096 个 ID。

线程安全：进程内全局单例 + ``threading.Lock``。本平台后端为 async
单进程多 worker，每个 Gunicorn worker 必须拥有不同的 ``worker_id``
（通过 ``GUNICORN_WORKER_ID`` 注入或配置不同副本）。
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Self

# 位宽（与上图一致）
_TIMESTAMP_BITS = 41
_DATACENTER_BITS = 5
_WORKER_BITS = 5
_SEQUENCE_BITS = 12

_MAX_DATACENTER_ID = (1 << _DATACENTER_BITS) - 1
_MAX_WORKER_ID = (1 << _WORKER_BITS) - 1
_MAX_SEQUENCE = (1 << _SEQUENCE_BITS) - 1

_DATACENTER_SHIFT = _SEQUENCE_BITS + _WORKER_BITS
_TIMESTAMP_SHIFT = _DATACENTER_SHIFT + _DATACENTER_BITS
_WORKER_SHIFT = _SEQUENCE_BITS


@dataclass
class _SnowflakeState:
    last_ms: int = -1
    sequence: int = 0


class SnowflakeGenerator:
    """雪花 ID 生成器（线程安全）。"""

    def __init__(self, *, datacenter_id: int, worker_id: int, epoch_ms: int) -> None:
        if not 0 <= datacenter_id <= _MAX_DATACENTER_ID:
            raise ValueError(f"datacenter_id 越界 [0,{_MAX_DATACENTER_ID}]")
        if not 0 <= worker_id <= _MAX_WORKER_ID:
            raise ValueError(f"worker_id 越界 [0,{_MAX_WORKER_ID}]")
        self._dc = datacenter_id
        self._wk = worker_id
        self._epoch = epoch_ms
        self._state = _SnowflakeState()
        self._lock = threading.Lock()

    def next_id(self) -> int:
        """生成下一个雪花 ID。"""
        with self._lock:
            now = self._now_ms()
            state = self._state
            if now < state.last_ms:
                # 回拨：等待时钟追上（或拒绝服务）。0~5ms 之内等，否则报错。
                if state.last_ms - now <= 5:
                    while now < state.last_ms:
                        now = self._now_ms()
                else:
                    raise RuntimeError(f"时钟回拨过大（{state.last_ms - now} ms），拒绝生成 ID")
            if now == state.last_ms:
                state.sequence = (state.sequence + 1) & _MAX_SEQUENCE
                if state.sequence == 0:
                    # 同一毫秒序列号耗尽，自旋到下一毫秒
                    while now <= state.last_ms:
                        now = self._now_ms()
            else:
                state.sequence = 0
            state.last_ms = now

            return (
                ((now - self._epoch) << _TIMESTAMP_SHIFT)
                | (self._dc << _DATACENTER_SHIFT)
                | (self._wk << _WORKER_SHIFT)
                | state.sequence
            )

    @staticmethod
    def _now_ms() -> int:
        return int(time.time() * 1000)

    @classmethod
    def from_settings(cls) -> Self:
        from app.core.config import get_settings

        s = get_settings().snowflake
        return cls(datacenter_id=s.datacenter_id, worker_id=s.worker_id, epoch_ms=s.epoch_ms)


# ── 全局单例（按需初始化） ─────────────────────────────────────
_generator: SnowflakeGenerator | None = None
_init_lock = threading.Lock()


def next_snowflake_id() -> int:
    """生成下一个雪花 ID（全局单例）。"""
    global _generator
    if _generator is None:
        with _init_lock:
            if _generator is None:
                _generator = SnowflakeGenerator.from_settings()
    return _generator.next_id()


def parse_snowflake_id(snowflake_id: int, *, epoch_ms: int | None = None) -> dict[str, int]:
    """解析雪花 ID（用于运维定位、调试）。"""
    if epoch_ms is None:
        from app.core.config import get_settings

        epoch_ms = get_settings().snowflake.epoch_ms
    timestamp_ms = (snowflake_id >> _TIMESTAMP_SHIFT) + epoch_ms
    datacenter_id = (snowflake_id >> _DATACENTER_SHIFT) & _MAX_DATACENTER_ID
    worker_id = (snowflake_id >> _WORKER_SHIFT) & _MAX_WORKER_ID
    sequence = snowflake_id & _MAX_SEQUENCE
    return {
        "timestamp_ms": timestamp_ms,
        "datacenter_id": datacenter_id,
        "worker_id": worker_id,
        "sequence": sequence,
    }
