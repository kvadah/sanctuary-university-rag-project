"""Celery tasks for background document ingestion.

Auto-discovered via ``celery_app.autodiscover_tasks(["app.workers"])``. The task
body is synchronous (Celery-facing); the actual work is async and is driven on the
worker's persistent event loop through :func:`run_async`. Each phase runs in its
own ``worker_session`` so the PROCESSING marker and the final COMPLETED/FAILED
status are committed independently of one another.
"""
import asyncio
import logging
import uuid
from typing import Optional

from app.models.audit import IndexingStatus
from app.models.knowledge import DocumentClassification
from app.repositories.indexing_job_repository import IndexingJobRepository
from app.services.ingestion_service import IngestionService, resolve_file_type
from app.utils import storage
from app.workers.celery_app import celery_app
from app.workers.runtime import run_async, worker_session

logger = logging.getLogger(__name__)


async def _ingest(
    *,
    job_id: uuid.UUID,
    object_key: str,
    filename: Optional[str],
    title: Optional[str],
    classification: DocumentClassification,
    academic_term: Optional[str],
    source_id: uuid.UUID,
) -> None:
    async with worker_session() as db:
        await IndexingJobRepository(db).set_status(
            job_id, IndexingStatus.PROCESSING
        )

    # Pull the archived original out of MinIO (sync SDK -> offload thread).
    data = await asyncio.to_thread(storage.get_object, object_key)

    # Canonical validation lives request-side; re-resolve here so the worker
    # relies on the same single source of truth rather than a private parse.
    file_type = resolve_file_type(filename)
    async with worker_session() as db:
        document, chunk_count = await IngestionService(db).ingest_bytes(
            data=data,
            file_type=file_type,
            source_id=source_id,
            title=title,
            filename=filename,
            classification=classification,
            academic_term=academic_term,
            file_path=object_key,
        )
        document_id = document.id  # capture before the session closes

    async with worker_session() as db:
        await IndexingJobRepository(db).set_completed(
            job_id, document_id=document_id, chunk_count=chunk_count
        )


@celery_app.task(name="ingest_document", bind=True)
def ingest_document(
    self,
    *,
    job_id: str,
    object_key: str,
    filename: Optional[str],
    title: Optional[str],
    classification: str,
    academic_term: Optional[str],
    source_id: str,
) -> dict:
    """Parse -> chunk -> embed -> store one uploaded document, updating its job."""
    job_uuid = uuid.UUID(job_id)
    try:
        run_async(
            _ingest(
                job_id=job_uuid,
                object_key=object_key,
                filename=filename,
                title=title,
                classification=DocumentClassification(classification),
                academic_term=academic_term,
                source_id=uuid.UUID(source_id),
            )
        )
    except Exception as exc:
        logger.exception("Indexing job %s failed", job_id)
        # Record the failure on the job (own session) so the UI can surface it.
        try:
            run_async(_mark_failed(job_uuid, str(exc)))
        except Exception:
            logger.exception("Could not mark job %s FAILED", job_id)
        raise  # let Celery record the task failure too

    return {"job_id": job_id, "status": IndexingStatus.COMPLETED.value}


async def _mark_failed(job_id: uuid.UUID, message: str) -> None:
    async with worker_session() as db:
        await IndexingJobRepository(db).set_failed(job_id, message)
