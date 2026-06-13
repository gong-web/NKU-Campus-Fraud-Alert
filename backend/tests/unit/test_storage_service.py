from __future__ import annotations

import hashlib
from io import BytesIO
from typing import ClassVar

import pytest

from app.core.config import StorageSettings
from app.services import storage_service


class MissingBucketError(Exception):
    response: ClassVar[dict[str, dict[str, str]]] = {"Error": {"Code": "NoSuchBucket"}}


class FakeS3Client:
    def __init__(self) -> None:
        self.bucket_exists = False
        self.objects: dict[str, bytes] = {}

    def head_bucket(self, *, Bucket: str) -> None:
        del Bucket
        if not self.bucket_exists:
            raise MissingBucketError

    def create_bucket(self, *, Bucket: str) -> None:
        del Bucket
        self.bucket_exists = True

    def put_object(self, *, Bucket: str, Key: str, Body: bytes, **kwargs: object) -> None:
        del Bucket, kwargs
        self.objects[Key] = Body

    def get_object(self, *, Bucket: str, Key: str) -> dict[str, BytesIO]:
        del Bucket
        return {"Body": BytesIO(self.objects[Key])}

    def delete_object(self, *, Bucket: str, Key: str) -> None:
        del Bucket
        self.objects.pop(Key, None)


@pytest.mark.asyncio
async def test_s3_storage_encrypts_roundtrips_and_deletes(monkeypatch) -> None:
    fake_s3 = FakeS3Client()
    raw = b"demo evidence bytes"

    monkeypatch.setattr(storage_service, "_S3_CLIENT", fake_s3)
    monkeypatch.setattr(storage_service, "_S3_BUCKET_READY", False)
    monkeypatch.setattr(
        storage_service,
        "_storage_settings",
        lambda: StorageSettings(backend="s3", bucket="evidence"),
    )

    storage_path, file_hash, key_version = await storage_service.save_evidence_file(
        entity_type="case",
        entity_id=123,
        file_id=456,
        raw_content=raw,
    )

    assert storage_path == "case/123/456.enc"
    assert file_hash == hashlib.sha256(raw).hexdigest()
    assert key_version == "v1"
    assert fake_s3.bucket_exists is True
    assert fake_s3.objects[storage_path] != raw

    assert await storage_service.read_evidence_file(storage_path) == raw

    await storage_service.delete_evidence_file(storage_path)
    assert storage_path not in fake_s3.objects
