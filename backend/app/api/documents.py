"""Document ingestion endpoints."""
import math
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import require_roles
from app.models.knowledge import DocumentClassification
from app.models.user import User, UserRole
from app.schemas.common import PaginationMeta
from app.schemas.knowledge import (
    DocumentListResponse,
    IndexingJobListResponse,
    IndexingJobRead,
)
from app.services.document_service import DocumentService
from app.services.ingestion_job_service import IngestionJobService

router = APIRouter(prefix="/documents", tags=["Documents"])

# Uploading (indexing) is a staff-level action; reads are any authenticated user.
UploadRoles = require_roles([UserRole.ADMIN, UserRole.FACULTY, UserRole.STAFF])
ReadRoles = require_roles(
    [UserRole.ADMIN, UserRole.FACULTY, UserRole.STAFF, UserRole.STUDENT]
)


@router.post(
    "/upload",
    response_model=IndexingJobRead,
    status_code=status.HTTP_202_ACCEPTED,
)
async def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    classification: DocumentClassification = Form(DocumentClassification.PUBLIC),
    academic_term: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(UploadRoles),
):
    """Archive the upload and enqueue background indexing; returns the queued job."""
    service = IngestionJobService(db)
    job = await service.enqueue_upload(
        file=file,
        title=title,
        classification=classification,
        academic_term=academic_term,
    )
    return IndexingJobRead.model_validate(job)


@router.get("/jobs", response_model=IndexingJobListResponse)
async def list_indexing_jobs(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(UploadRoles),
):
    """Recent indexing jobs, newest first (polled while any are in flight)."""
    service = IngestionJobService(db)
    jobs = await service.list_recent(limit=limit)
    return IndexingJobListResponse(
        items=[IndexingJobRead.model_validate(j) for j in jobs]
    )


@router.get("/jobs/{job_id}", response_model=IndexingJobRead)
async def get_indexing_job(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(UploadRoles),
):
    """Fetch a single indexing job by id (404 if it does not exist)."""
    service = IngestionJobService(db)
    job = await service.get_or_404(job_id)
    return IndexingJobRead.model_validate(job)


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(ReadRoles),
):
    """List indexed documents, newest first (paginated)."""
    service = DocumentService(db)
    items, total = await service.list_documents(page=page, page_size=page_size)
    return DocumentListResponse(
        items=items,
        pagination=PaginationMeta(
            page=page,
            page_size=page_size,
            total_items=total,
            total_pages=math.ceil(total / page_size) if total else 0,
        ),
    )
