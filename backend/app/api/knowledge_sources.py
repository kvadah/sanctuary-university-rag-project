import math
import uuid
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import get_db
from app.core.deps import require_roles
from app.models.user import User, UserRole
from app.schemas.common import PaginationMeta
from app.schemas.knowledge import (
    KnowledgeSourceCreate,
    KnowledgeSourceUpdate,
    KnowledgeSourceRead,
    KnowledgeSourceListResponse,
)
from app.services.knowledge_service import KnowledgeService

router = APIRouter(prefix="/knowledge-sources", tags=["Knowledge Sources"])

# Reads: any staff-level role; writes: admins only (API spec §5, §18).
ReadRoles = require_roles([UserRole.ADMIN, UserRole.FACULTY, UserRole.STAFF])
WriteRoles = require_roles([UserRole.ADMIN])


@router.post("", response_model=KnowledgeSourceRead, status_code=status.HTTP_201_CREATED)
async def create_knowledge_source(
    payload: KnowledgeSourceCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(WriteRoles),
):
    """Register a new knowledge source (Admin only)."""
    service = KnowledgeService(db)
    return await service.create_source(payload)


@router.get("", response_model=KnowledgeSourceListResponse)
async def list_knowledge_sources(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(ReadRoles),
):
    """List configured knowledge sources, newest first (paginated)."""
    service = KnowledgeService(db)
    items, total = await service.list_sources(page=page, page_size=page_size)
    return KnowledgeSourceListResponse(
        items=items,
        pagination=PaginationMeta(
            page=page,
            page_size=page_size,
            total_items=total,
            total_pages=math.ceil(total / page_size) if total else 0,
        ),
    )


@router.get("/{source_id}", response_model=KnowledgeSourceRead)
async def get_knowledge_source(
    source_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(ReadRoles),
):
    """Retrieve a single knowledge source by id."""
    service = KnowledgeService(db)
    return await service.get_source(source_id)


@router.patch("/{source_id}", response_model=KnowledgeSourceRead)
async def update_knowledge_source(
    source_id: uuid.UUID,
    payload: KnowledgeSourceUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(WriteRoles),
):
    """Partially update a knowledge source (Admin only)."""
    service = KnowledgeService(db)
    return await service.update_source(source_id, payload)


@router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_knowledge_source(
    source_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(WriteRoles),
):
    """Delete a knowledge source and its documents (Admin only)."""
    service = KnowledgeService(db)
    await service.delete_source(source_id)
