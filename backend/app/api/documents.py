"""Document ingestion endpoints."""
import math
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import require_roles
from app.models.knowledge import DocumentClassification
from app.models.user import User, UserRole
from app.schemas.common import PaginationMeta
from app.schemas.knowledge import (
    DocumentIngestResponse,
    DocumentListResponse,
    DocumentRead,
)
from app.services.document_service import DocumentService
from app.services.ingestion_service import IngestionService

router = APIRouter(prefix="/documents", tags=["Documents"])

# Uploading (indexing) is a staff-level action; reads are any authenticated user.
UploadRoles = require_roles([UserRole.ADMIN, UserRole.FACULTY, UserRole.STAFF])
ReadRoles = require_roles(
    [UserRole.ADMIN, UserRole.FACULTY, UserRole.STAFF, UserRole.STUDENT]
)


@router.post(
    "/upload",
    response_model=DocumentIngestResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    classification: DocumentClassification = Form(DocumentClassification.PUBLIC),
    academic_term: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(UploadRoles),
):
    """Upload and index a PDF/DOCX/TXT document (parse -> chunk -> embed -> store)."""
    service = IngestionService(db)
    document, chunk_count = await service.ingest_upload(
        file=file,
        title=title,
        classification=classification,
        academic_term=academic_term,
    )
    return DocumentIngestResponse(
        document=DocumentRead.model_validate(document), chunk_count=chunk_count
    )


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
