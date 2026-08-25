"""Request-side orchestration for background document ingestion.

Turns an upload into (1) an archived original in MinIO and (2) a queued Celery
job tracked by an :class:`IndexingJob` row the frontend polls. The heavy pipeline
runs in the worker (see ``app.workers.tasks``); this returns as soon as the job
is enqueued.
"""
import uuid
from typing import List, Optional

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.models.audit import IndexingJob
from app.models.knowledge import DocumentClassification
from app.repositories.indexing_job_repository import IndexingJobRepository
from app.repositories.knowledge_repository import KnowledgeSourceRepository
from app.services.ingestion_service import resolve_file_type, source_type_for
from app.utils import storage
from app.workers.celery_app import celery_app


class IngestionJobService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.jobs = IndexingJobRepository(db)
        self.sources = KnowledgeSourceRepository(db)

    async def enqueue_upload(
        self,
        *,
        file: UploadFile,
        title: Optional[str],
        classification: DocumentClassification,
        academic_term: Optional[str],
    ) -> IndexingJob:
        # Validate up front so a bad upload 400s without ever creating a job.
        file_type = resolve_file_type(file.filename)
        data = await file.read()
        if not data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty.",
            )

        source = await self.sources.get_or_create_upload_source(
            source_type_for(file_type)
        )
        job = await self.jobs.create(
            source_id=source.id, original_filename=file.filename
        )
        # Commit so the row is durable before the worker can race to read it.
        await self.db.commit()

        object_key = storage.build_object_key(str(job.id), file.filename)
        try:
            await run_in_threadpool(storage.ensure_bucket)
            await run_in_threadpool(
                storage.put_object,
                object_key,
                data,
                file.content_type or "application/octet-stream",
            )
            celery_app.send_task(
                "ingest_document",
                kwargs={
                    "job_id": str(job.id),
                    "object_key": object_key,
                    "filename": file.filename,
                    "title": title,
                    "classification": classification.value,
                    "academic_term": academic_term,
                    "source_id": str(source.id),
                },
            )
        except Exception as exc:  # storage down / broker unreachable
            await self.jobs.set_failed(job.id, f"Failed to enqueue job: {exc}")
            await self.db.commit()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not start indexing. Please try again.",
            )

        return job

    async def list_recent(self, limit: int = 20) -> List[IndexingJob]:
        """Recent jobs, newest first (for the documents table and admin card)."""
        return await self.jobs.list_recent(limit=limit)

    async def get_or_404(self, job_id: uuid.UUID) -> IndexingJob:
        job = await self.jobs.get_by_id(job_id)
        if job is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Job not found."
            )
        return job
