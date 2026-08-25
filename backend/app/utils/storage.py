"""MinIO object storage for original uploaded files.

Thin wrapper over the (synchronous) MinIO SDK. The request path must call these
via ``run_in_threadpool`` so the event loop is not blocked; the Celery worker is
synchronous and calls them via ``asyncio.to_thread``. The bucket is created
lazily and idempotently, so no startup hook is required.
"""
import io
from functools import lru_cache

from minio import Minio

from app.core.config import settings


@lru_cache(maxsize=1)
def _client() -> Minio:
    return Minio(
        settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=settings.MINIO_SECURE,
    )


def build_object_key(job_id: str, filename: str) -> str:
    """Namespace each upload under its job id: ``uploads/{job_id}/{filename}``."""
    safe = (filename or "upload").replace("/", "_").replace("\\", "_")
    return f"uploads/{job_id}/{safe}"


def ensure_bucket() -> None:
    """Create the documents bucket if it does not already exist (idempotent)."""
    client = _client()
    bucket = settings.MINIO_BUCKET_DOCUMENTS
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)


def put_object(
    key: str, data: bytes, content_type: str = "application/octet-stream"
) -> str:
    """Store ``data`` at ``key`` and return the key."""
    _client().put_object(
        settings.MINIO_BUCKET_DOCUMENTS,
        key,
        io.BytesIO(data),
        length=len(data),
        content_type=content_type,
    )
    return key


def get_object(key: str) -> bytes:
    """Fetch the bytes stored at ``key``."""
    response = _client().get_object(settings.MINIO_BUCKET_DOCUMENTS, key)
    try:
        return response.read()
    finally:
        response.close()
        response.release_conn()
