"""密钥管理服务（KMS）抽象层。

设计目标
--------
- L3 高敏字段（手机号、邮箱、AnonymousMapping）的加密密钥**必须**由 KMS
  独立托管，不与密文同库。
- 应用层只能通过 :class:`KMSClient` 拿到当前 ``data key``，**永远拿不到**
  主密钥。
- 支持 ``encryption_key_version`` 字段标记密钥版本，便于在线轮转。

实现
----
- :class:`LocalKMS`：从环境变量读 base64 主密钥派生 data key（仅 dev/test）。
- :class:`VaultKMS`：通过 HTTP API 调学校 Vault（生产推荐）。占位实现。
- :class:`AWSKMS`：调 AWS KMS（备选）。占位实现。

用法
----
.. code-block:: python

    from app.core.kms import get_kms_client

    kms = get_kms_client()
    dek = kms.get_data_key("v1")          # 拿 32 字节 DEK
    cipher = aes_gcm_encrypt(plain, dek)  # 用 DEK 加密
"""

from __future__ import annotations

import base64
import hashlib
import hmac
from abc import ABC, abstractmethod
from functools import lru_cache

from app.core.config import KMSSettings, get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# 派生 DEK 用的 HKDF info
_DEK_INFO = b"anti-fraud:field-encryption:dek"
_DEK_LEN = 32  # AES-256


class KMSError(Exception):
    """KMS 通用错误。"""


class KMSClient(ABC):
    """密钥管理客户端抽象。

    Attributes:
        provider_name: provider 标识，写入审计日志便于审查。
    """

    provider_name: str

    @abstractmethod
    def get_data_key(self, version: str) -> bytes:
        """返回指定版本的 32 字节 DEK。"""

    @abstractmethod
    def current_version(self) -> str:
        """当前推荐使用的 DEK 版本。"""


class LocalKMS(KMSClient):
    """本地主密钥派生 DEK（仅 dev / test 用）。

    通过 HKDF（HMAC-SHA256）从 ``KMS_LOCAL_MASTER_KEY`` 派生 32 字节 DEK，
    salt 取版本号字符串。**严禁生产使用**。
    """

    provider_name = "local"

    def __init__(self, master_key_b64: str, current_version: str) -> None:
        try:
            self._master_key = base64.b64decode(master_key_b64, validate=True)
        except (ValueError, base64.binascii.Error) as exc:  # type: ignore[attr-defined]
            raise KMSError("KMS_LOCAL_MASTER_KEY 必须为 base64") from exc
        if len(self._master_key) < 16:
            raise KMSError("KMS_LOCAL_MASTER_KEY 解码后长度不足 16 字节")
        self._version = current_version

    def get_data_key(self, version: str) -> bytes:
        salt = version.encode("utf-8")
        return _hkdf(self._master_key, salt=salt, info=_DEK_INFO, length=_DEK_LEN)

    def current_version(self) -> str:
        return self._version


class VaultKMS(KMSClient):
    """学校 Vault KMS。

    占位实现：实际部署时填入 Vault 地址、AppRole、token、transit engine 路径。
    """

    provider_name = "vault"

    def __init__(self) -> None:
        raise KMSError(
            "VaultKMS 尚未启用，请先在 infra/vault 中配置 Vault transit engine "
            "并实现 _fetch_dek()。当前提交是骨架占位。"
        )

    def get_data_key(self, version: str) -> bytes:
        raise NotImplementedError

    def current_version(self) -> str:
        raise NotImplementedError


class AWSKMS(KMSClient):
    """AWS KMS。"""

    provider_name = "aws"

    def __init__(self) -> None:
        raise KMSError("AWSKMS 暂未实现，骨架占位。")

    def get_data_key(self, version: str) -> bytes:
        raise NotImplementedError

    def current_version(self) -> str:
        raise NotImplementedError


# ── HKDF（RFC 5869，使用 hmac-sha256）────────────────────────────
def _hkdf(ikm: bytes, *, salt: bytes, info: bytes, length: int) -> bytes:
    """HKDF (extract + expand)。"""
    if not salt:
        salt = b"\x00" * hashlib.sha256().digest_size
    prk = hmac.new(salt, ikm, hashlib.sha256).digest()
    okm = b""
    block = b""
    counter = 1
    while len(okm) < length:
        block = hmac.new(prk, block + info + bytes([counter]), hashlib.sha256).digest()
        okm += block
        counter += 1
    return okm[:length]


@lru_cache(maxsize=1)
def get_kms_client() -> KMSClient:
    """获取当前 KMS 客户端（按配置切换）。"""
    s: KMSSettings = get_settings().kms
    if s.provider == "local":
        if get_settings().app_env == "prod":
            raise KMSError("生产环境禁止使用 LocalKMS")
        logger.warning("kms_provider_local", note="仅 dev/test 可用，生产必须切换")
        return LocalKMS(
            master_key_b64=s.local_master_key.get_secret_value(),
            current_version=s.data_key_version,
        )
    if s.provider == "vault":
        return VaultKMS()
    if s.provider == "aws":
        return AWSKMS()
    raise KMSError(f"未知 KMS provider: {s.provider}")
