"""安全工具：AES-256-GCM 字段加密、HMAC 签名、随机数。

PRD 5.5.2 要求：
- L3 字段（手机号、邮箱、匿名身份）使用 AES-256-GCM 加密
- 加密所用 DEK 由独立 KMS 托管
- 通过 ``encryption_key_version`` 字段记录密钥版本，支持在线轮转

存储格式
--------
密文格式 = ``version (1B) | iv (12B) | ciphertext | tag (16B)``，全部 raw bytes。
``version`` 是 KMS 中 DEK 的版本号映射到一个字节（"v1" → 1）。
"""

from __future__ import annotations

import hmac
import os
import secrets
from dataclasses import dataclass

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.kms import KMSClient, get_kms_client

_IV_LEN = 12
_TAG_LEN = 16
_VERSION_HEADER_LEN = 1


class CryptoError(Exception):
    """加解密失败。"""


@dataclass(frozen=True)
class EncryptedField:
    """加密后的字段，可直接落库到 ``VARBINARY``。"""

    payload: bytes
    """version | iv | ciphertext | tag"""

    version: str
    """对应 KMS DEK 版本（如 'v1'）"""

    @property
    def length(self) -> int:
        return len(self.payload)


def _version_to_byte(version: str) -> int:
    """将 'v1' → 1，'v15' → 15。仅支持 ``v\\d+`` 格式。"""
    if not version.startswith("v") or not version[1:].isdigit():
        raise CryptoError(f"非法 KMS 版本号: {version}")
    n = int(version[1:])
    if not 0 < n < 256:
        raise CryptoError(f"KMS 版本号溢出 1 字节: {version}")
    return n


def _byte_to_version(b: int) -> str:
    if not 0 < b < 256:
        raise CryptoError(f"密文头版本字节越界: {b}")
    return f"v{b}"


def encrypt_field(plaintext: str | bytes, *, kms: KMSClient | None = None) -> EncryptedField:
    """加密一个字段；返回 ``EncryptedField``。"""
    kms = kms or get_kms_client()
    version = kms.current_version()
    dek = kms.get_data_key(version)
    if isinstance(plaintext, str):
        plaintext = plaintext.encode("utf-8")
    iv = os.urandom(_IV_LEN)
    aesgcm = AESGCM(dek)
    aad = version.encode("utf-8")
    ciphertext = aesgcm.encrypt(iv, plaintext, aad)
    payload = bytes([_version_to_byte(version)]) + iv + ciphertext
    return EncryptedField(payload=payload, version=version)


def decrypt_field(payload: bytes, *, kms: KMSClient | None = None) -> bytes:
    """解密一个字段；返回明文字节。"""
    kms = kms or get_kms_client()
    if len(payload) < _VERSION_HEADER_LEN + _IV_LEN + _TAG_LEN:
        raise CryptoError("密文长度过短，可能被截断或损坏")
    version = _byte_to_version(payload[0])
    iv = payload[_VERSION_HEADER_LEN : _VERSION_HEADER_LEN + _IV_LEN]
    ct = payload[_VERSION_HEADER_LEN + _IV_LEN :]
    dek = kms.get_data_key(version)
    aesgcm = AESGCM(dek)
    aad = version.encode("utf-8")
    try:
        return aesgcm.decrypt(iv, ct, aad)
    except Exception as exc:  # cryptography 抛 InvalidTag 等
        raise CryptoError("AES-GCM 解密失败：密文被篡改或密钥不匹配") from exc


# ── HMAC 工具 ──────────────────────────────────────────────────────
def hmac_sha256(data: bytes, *, key: bytes) -> bytes:
    """HMAC-SHA256（用于审计哈希链）。"""
    return hmac.new(key, data, "sha256").digest()


def constant_time_eq(a: bytes, b: bytes) -> bool:
    """常量时间比较（防计时攻击）。"""
    return hmac.compare_digest(a, b)


# ── 安全随机 ────────────────────────────────────────────────────────
def generate_session_id() -> str:
    """UUID v4（不可预测，防会话固定攻击）。

    见 PRD 5.4.1 用户自定义完整性 - Session：CHAR(36)。
    """
    import uuid

    return str(uuid.uuid4())


def generate_secret_token(length_bytes: int = 32) -> str:
    """密钥学安全的随机 URL-safe token（idempotency-key、nonce 等用）。"""
    return secrets.token_urlsafe(length_bytes)
