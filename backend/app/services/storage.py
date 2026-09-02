"""
Legal Lens - Storage Abstraction (Phase 6: docs/PRODUCTION_READINESS_PRD.md)

S3_BUCKET unset (local/dev/tests): files live under STORAGE_DIR on
local disk, served by the existing /uploads static mount - zero setup,
identical to pre-Phase-6 behavior.

S3_BUCKET set (docker-compose's minio service, or real S3/MinIO):
files live in that bucket. Reads are cached to a local dir on first
access, since OCR (OpenCV/Tesseract) needs a real file on disk to
read - this trades a one-time download per file for keeping the OCR
pipeline untouched.

Everywhere else in the codebase stores/reads a plain relative `key`
(e.g. "images/products/INS-0001_front_123.jpg", "reports/RPT-1.pdf"),
never a full path or URL - that's what makes both backends
interchangeable.
"""
import os
import shutil
from abc import ABC, abstractmethod
from typing import BinaryIO, Optional
from ..core.config import STORAGE_DIR


class StorageBackend(ABC):
    @abstractmethod
    def save(self, file_obj: BinaryIO, key: str) -> None:
        """Write an uploaded file's bytes to `key`."""

    @abstractmethod
    def save_local_file(self, local_path: str, key: str) -> None:
        """Adopt a file already written to local disk (e.g. a
        reportlab-generated PDF) into this backend under `key`."""

    @abstractmethod
    def local_path(self, key: str) -> Optional[str]:
        """A real filesystem path for `key` (downloading/caching first if needed), or None if it doesn't exist."""

    @abstractmethod
    def url(self, key: str) -> str:
        """A URL a browser can fetch `key` from directly."""


class LocalStorageBackend(StorageBackend):
    def __init__(self, root: str):
        self.root = root

    def _full_path(self, key: str) -> str:
        return os.path.join(self.root, key)

    def save(self, file_obj, key):
        full = self._full_path(key)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "wb") as f:
            shutil.copyfileobj(file_obj, f)

    def save_local_file(self, local_path, key):
        full = self._full_path(key)
        if os.path.abspath(local_path) == os.path.abspath(full):
            return  # already written straight to the right place
        os.makedirs(os.path.dirname(full), exist_ok=True)
        shutil.copyfile(local_path, full)

    def local_path(self, key):
        full = self._full_path(key)
        return full if os.path.exists(full) else None

    def url(self, key):
        return f"/uploads/{key}"


class S3StorageBackend(StorageBackend):
    def __init__(self, bucket: str, endpoint_url: Optional[str], cache_dir: str):
        import boto3  # optional dependency, only imported when S3 is actually configured
        self.bucket = bucket
        self.cache_dir = cache_dir
        self.client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=os.environ.get("S3_ACCESS_KEY"),
            aws_secret_access_key=os.environ.get("S3_SECRET_KEY"),
            region_name=os.environ.get("S3_REGION", "us-east-1"),
        )

    def _cache_path(self, key: str) -> str:
        return os.path.join(self.cache_dir, key)

    def save(self, file_obj, key):
        self.client.upload_fileobj(file_obj, self.bucket, key)

    def save_local_file(self, local_path, key):
        self.client.upload_file(local_path, self.bucket, key)

    def local_path(self, key):
        cached = self._cache_path(key)
        if os.path.exists(cached):
            return cached
        os.makedirs(os.path.dirname(cached), exist_ok=True)
        try:
            self.client.download_file(self.bucket, key, cached)
            return cached
        except Exception:
            return None

    def url(self, key):
        return self.client.generate_presigned_url(
            "get_object", Params={"Bucket": self.bucket, "Key": key}, ExpiresIn=3600
        )


def _build_storage() -> StorageBackend:
    bucket = os.environ.get("S3_BUCKET")
    if bucket:
        return S3StorageBackend(
            bucket=bucket,
            endpoint_url=os.environ.get("S3_ENDPOINT_URL"),
            cache_dir=os.path.join(STORAGE_DIR, ".s3-cache"),
        )
    return LocalStorageBackend(root=STORAGE_DIR)


storage = _build_storage()
