"""Repository for indexing jobs (async DB access only).

Tracks the lifecycle of a background ingestion job so the frontend can poll it:
PENDING -> PROCESSING -> COMPLETED | FAILED. Written from both the request side
(job creation) and the Celery worker (status transitions).
"""
import uuid
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import IndexingJob, IndexingStatus


class IndexingJobRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        *,
        source_id: uuid.UUID,
        original_filename: Optional[str],
        total_documents: int = 1,
    ) -> IndexingJob:
        """Create a PENDING job (id assigned on flush)."""
        job = IndexingJob(
            source_id=source_id,
            status=IndexingStatus.PENDING.value,
            total_documents=total_documents,
            processed_documents=0,
            chunk_count=0,
            original_filename=original_filename,
        )
        self.db.add(job)
        await self.db.flush()
        await self.db.refresh(job)
        return job

    async def get_by_id(self, job_id: uuid.UUID) -> Optional[IndexingJob]:
        result = await self.db.execute(
            select(IndexingJob).where(IndexingJob.id == job_id)
        )
        return result.scalar_one_or_none()

    async def list_recent(self, limit: int = 20) -> List[IndexingJob]:
        """Most recent jobs first (for the documents table and admin card)."""
        result = await self.db.execute(
            select(IndexingJob)
            .order_by(IndexingJob.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def set_status(
        self, job_id: uuid.UUID, status: IndexingStatus
    ) -> Optional[IndexingJob]:
        job = await self.get_by_id(job_id)
        if job is None:
            return None
        job.status = status.value
        await self.db.flush()
        return job

    async def set_completed(
        self, job_id: uuid.UUID, *, document_id: uuid.UUID, chunk_count: int
    ) -> Optional[IndexingJob]:
        job = await self.get_by_id(job_id)
        if job is None:
            return None
        job.status = IndexingStatus.COMPLETED.value
        job.document_id = document_id
        job.chunk_count = chunk_count
        job.processed_documents = job.total_documents
        job.error_message = None
        await self.db.flush()
        return job

    async def set_failed(
        self, job_id: uuid.UUID, error_message: str
    ) -> Optional[IndexingJob]:
        job = await self.get_by_id(job_id)
        if job is None:
            return None
        job.status = IndexingStatus.FAILED.value
        job.error_message = error_message[:2000]
        await self.db.flush()
        return job
