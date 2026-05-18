"""证据文件存储服务（UC-01）。

文件上传后用 AES-256-GCM 加密再存盘（满足 PRD 5.5.2 L3 字段加密要求）。
存储目录通过环境变量 EVIDENCE_UPLOAD_DIR 配置，默认 /app/uploads/evidence。
"""

from __future__ import annotations

import asyncio
import hashlib
import os
from pathlib import Path

from app.core.logging import get_logger
from app.core.security import decrypt_field, encrypt_field

logger = get_logger(__name__)

_UPLOAD_DIR: Path | None = None

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
MAX_FILES_PER_CASE = 10
ALLOWED_MIME_TYPES: frozenset[str] = frozenset(
    {
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/webp",
        "image/bmp",
        "image/tiff",
        "application/pdf",
    }
)


def get_upload_dir() -> Path:
    global _UPLOAD_DIR
    if _UPLOAD_DIR is None:
        _UPLOAD_DIR = Path(os.getenv("EVIDENCE_UPLOAD_DIR", "/app/uploads/evidence"))
    return _UPLOAD_DIR


async def save_evidence_file(
    *,
    entity_type: str,
    entity_id: int,
    file_id: int,
    raw_content: bytes,
) -> tuple[str, str, str]:
    """加密并写入文件。

    Args:
        entity_type: ``"case"`` 或 ``"draft"``
        entity_id: case_id 或 draft_id
        file_id: 雪花 ID（用作文件名）
        raw_content: 原始文件字节

    Returns:
        ``(storage_path, sha256_hex, key_version)``
    """
    file_hash = hashlib.sha256(raw_content).hexdigest()
    encrypted = encrypt_field(raw_content)

    rel_path = f"{entity_type}/{entity_id}/{file_id}.enc"
    abs_path = get_upload_dir() / rel_path

    loop = asyncio.get_event_loop()

    def _write() -> None:
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        abs_path.write_bytes(encrypted.payload)

    await loop.run_in_executor(None, _write)
    logger.debug("evidence_saved", path=rel_path, size=len(raw_content))
    return rel_path, file_hash, encrypted.version


async def read_evidence_file(storage_path: str) -> bytes:
    """解密并读取文件，返回原始明文字节。"""
    abs_path = get_upload_dir() / storage_path

    loop = asyncio.get_event_loop()
    encrypted_bytes: bytes = await loop.run_in_executor(None, abs_path.read_bytes)
    return decrypt_field(encrypted_bytes)


async def delete_evidence_file(storage_path: str) -> None:
    """删除加密文件（草稿删除时调用）。"""
    abs_path = get_upload_dir() / storage_path
    loop = asyncio.get_event_loop()

    def _remove() -> None:
        if abs_path.exists():
            abs_path.unlink()

    await loop.run_in_executor(None, _remove)
