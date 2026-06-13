"""证据文件存储服务（UC-01）。

文件上传后统一用 AES-256-GCM 加密，再按配置写入本地目录或 MinIO/S3。
本地目录用于测试和轻量演示；Docker/生产化环境可通过 ``STORAGE_BACKEND=s3``
把加密后的对象写入兼容 S3 的对象存储。
"""

from __future__ import annotations

import asyncio
import hashlib
import os
from pathlib import Path
from typing import Any

from app.core.config import StorageSettings, get_settings
from app.core.logging import get_logger
from app.core.security import decrypt_field, encrypt_field
from app.exceptions import StorageError

logger = get_logger(__name__)

_UPLOAD_DIR: Path | None = None
_S3_CLIENT: Any | None = None
_S3_BUCKET_READY = False

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


def _storage_settings() -> StorageSettings:
    return get_settings().storage


def _get_s3_client() -> Any:
    global _S3_CLIENT
    if _S3_CLIENT is None:
        import boto3

        settings = _storage_settings()
        _S3_CLIENT = boto3.client(
            "s3",
            endpoint_url=settings.endpoint,
            aws_access_key_id=settings.access_key.get_secret_value(),
            aws_secret_access_key=settings.secret_key.get_secret_value(),
            region_name=settings.region,
            use_ssl=settings.use_ssl,
        )
    return _S3_CLIENT


def _is_missing_bucket_error(exc: Exception) -> bool:
    response = getattr(exc, "response", None)
    if not isinstance(response, dict):
        return False
    error = response.get("Error")
    if not isinstance(error, dict):
        return False
    code = str(error.get("Code", ""))
    return code in {"404", "NoSuchBucket", "NotFound"}


def _wrap_storage_error(action: str, exc: Exception) -> StorageError:
    logger.warning("object_storage_failed", action=action, error=str(exc))
    return StorageError(
        f"对象存储服务调用失败：{action}",
        details={"backend": _storage_settings().backend},
    )


def _ensure_s3_bucket() -> None:
    global _S3_BUCKET_READY
    if _S3_BUCKET_READY:
        return

    settings = _storage_settings()
    client = _get_s3_client()
    try:
        client.head_bucket(Bucket=settings.bucket)
    except Exception as exc:
        if not _is_missing_bucket_error(exc):
            raise _wrap_storage_error("检查存储桶", exc) from exc
        create_kwargs: dict[str, Any] = {"Bucket": settings.bucket}
        if settings.region != "us-east-1":
            create_kwargs["CreateBucketConfiguration"] = {
                "LocationConstraint": settings.region
            }
        try:
            client.create_bucket(**create_kwargs)
        except Exception as create_exc:
            raise _wrap_storage_error("创建存储桶", create_exc) from create_exc
    _S3_BUCKET_READY = True


def _save_to_s3(storage_path: str, payload: bytes) -> None:
    settings = _storage_settings()
    client = _get_s3_client()
    _ensure_s3_bucket()
    put_kwargs: dict[str, Any] = {
        "Bucket": settings.bucket,
        "Key": storage_path,
        "Body": payload,
        "ContentType": "application/octet-stream",
    }
    if settings.server_side_encryption:
        put_kwargs["ServerSideEncryption"] = "AES256"
    try:
        client.put_object(**put_kwargs)
    except Exception as exc:
        raise _wrap_storage_error("写入证据对象", exc) from exc


def _read_from_s3(storage_path: str) -> bytes:
    settings = _storage_settings()
    client = _get_s3_client()
    try:
        obj = client.get_object(Bucket=settings.bucket, Key=storage_path)
        return obj["Body"].read()
    except Exception as exc:
        raise _wrap_storage_error("读取证据对象", exc) from exc


def _delete_from_s3(storage_path: str) -> None:
    settings = _storage_settings()
    client = _get_s3_client()
    try:
        client.delete_object(Bucket=settings.bucket, Key=storage_path)
    except Exception as exc:
        raise _wrap_storage_error("删除证据对象", exc) from exc


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
    loop = asyncio.get_running_loop()

    def _write_local() -> None:
        abs_path = get_upload_dir() / rel_path
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        abs_path.write_bytes(encrypted.payload)

    if _storage_settings().backend == "s3":
        await loop.run_in_executor(None, _save_to_s3, rel_path, encrypted.payload)
    else:
        await loop.run_in_executor(None, _write_local)
    logger.debug(
        "evidence_saved",
        backend=_storage_settings().backend,
        path=rel_path,
        size=len(raw_content),
    )
    return rel_path, file_hash, encrypted.version


async def read_evidence_file(storage_path: str) -> bytes:
    """解密并读取文件，返回原始明文字节。"""
    loop = asyncio.get_running_loop()

    if _storage_settings().backend == "s3":
        encrypted_bytes: bytes = await loop.run_in_executor(None, _read_from_s3, storage_path)
    else:
        abs_path = get_upload_dir() / storage_path
        encrypted_bytes = await loop.run_in_executor(None, abs_path.read_bytes)
    return decrypt_field(encrypted_bytes)


async def delete_evidence_file(storage_path: str) -> None:
    """删除加密文件（草稿删除时调用）。"""
    loop = asyncio.get_running_loop()

    def _remove() -> None:
        abs_path = get_upload_dir() / storage_path
        if abs_path.exists():
            abs_path.unlink()

    if _storage_settings().backend == "s3":
        await loop.run_in_executor(None, _delete_from_s3, storage_path)
    else:
        await loop.run_in_executor(None, _remove)
