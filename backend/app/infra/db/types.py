"""自定义 SQLAlchemy 类型。

:class:`EncryptedBinary` 把 :func:`app.core.security.encrypt_field` 与
:func:`decrypt_field` 织入 SQLAlchemy 的 ``TypeDecorator``，实现"业务层无感
的字段级加密"——你只 ``user.email = "x@y.com"``，落库时自动 AES-GCM 加密；
读出来直接拿明文。

PRD 5.5.2 要求所有 L3 字段（手机号、邮箱、AnonymousMapping）走此通道。
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import VARBINARY, Dialect
from sqlalchemy.types import TypeDecorator

from app.core.security import decrypt_field, encrypt_field


class EncryptedBinary(TypeDecorator[str]):
    """``str`` ↔ ``VARBINARY``（AES-256-GCM）。"""

    impl = VARBINARY
    cache_ok = True

    def __init__(self, length: int = 512) -> None:
        super().__init__(length=length)

    def process_bind_param(self, value: Any, _: Dialect) -> bytes | None:
        if value is None:
            return None
        if not isinstance(value, str):
            value = str(value)
        return encrypt_field(value).payload

    def process_result_value(self, value: Any, _: Dialect) -> str | None:
        if value is None:
            return None
        return decrypt_field(value).decode("utf-8")
