"""AES-256-GCM 字段加密 + HKDF + 雪花 ID 单元测试。"""

from __future__ import annotations

import pytest

from app.core.security import (
    CryptoError,
    decrypt_field,
    encrypt_field,
    generate_session_id,
)
from app.core.snowflake import SnowflakeGenerator, parse_snowflake_id


class TestEncryption:
    def test_round_trip_str(self) -> None:
        e = encrypt_field("13800138000")
        assert decrypt_field(e.payload).decode() == "13800138000"

    def test_round_trip_bytes(self) -> None:
        e = encrypt_field(b"hello-world")
        assert decrypt_field(e.payload) == b"hello-world"

    def test_unique_iv_each_call(self) -> None:
        a = encrypt_field("same-input")
        b = encrypt_field("same-input")
        assert a.payload != b.payload  # IV 不同 → 密文不同

    def test_tamper_detected(self) -> None:
        e = encrypt_field("13800138000")
        tampered = bytearray(e.payload)
        tampered[-1] ^= 0xFF
        with pytest.raises(CryptoError):
            decrypt_field(bytes(tampered))

    def test_truncated_payload(self) -> None:
        with pytest.raises(CryptoError):
            decrypt_field(b"\x01" * 5)


class TestSnowflake:
    def test_monotonic(self) -> None:
        gen = SnowflakeGenerator(datacenter_id=1, worker_id=1, epoch_ms=1_000_000_000_000)
        ids = [gen.next_id() for _ in range(1000)]
        assert ids == sorted(ids)
        assert len(set(ids)) == 1000

    def test_parse(self) -> None:
        gen = SnowflakeGenerator(datacenter_id=3, worker_id=7, epoch_ms=1_000_000_000_000)
        sid = gen.next_id()
        parsed = parse_snowflake_id(sid, epoch_ms=1_000_000_000_000)
        assert parsed["datacenter_id"] == 3
        assert parsed["worker_id"] == 7

    def test_invalid_ids(self) -> None:
        with pytest.raises(ValueError):
            SnowflakeGenerator(datacenter_id=999, worker_id=1, epoch_ms=0)
        with pytest.raises(ValueError):
            SnowflakeGenerator(datacenter_id=0, worker_id=999, epoch_ms=0)


class TestSessionId:
    def test_uuid4_format(self) -> None:
        sid = generate_session_id()
        # UUIDv4：第 13 位 char 应为 '4'
        assert sid[14] == "4"
        assert len(sid) == 36
