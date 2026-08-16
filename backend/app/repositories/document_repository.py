"""Repositories for documents and their chunks (DB access only)."""
import uuid
from typing import List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge import Document, DocumentChunk, DocumentClassification


class DocumentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        *,
        source_id: uuid.UUID,
        title: str,
        file_type: str,
        classification: DocumentClassification,
        academic_term: Optional[str] = None,
        file_path: Optional[str] = None,
        url: Optional[str] = None,
        meta_data: Optional[dict] = None,
    ) -> Document:
        document = Document(
            source_id=source_id,
            title=title,
            file_type=file_type,
            classification=classification,
            academic_term=academic_term,
            file_path=file_path,
            url=url,
            meta_data=meta_data,
        )
        self.db.add(document)
        await self.db.flush()
        await self.db.refresh(document)
        return document

    async def get_by_id(self, document_id: uuid.UUID) -> Optional[Document]:
        result = await self.db.execute(
            select(Document).where(Document.id == document_id)
        )
        return result.scalar_one_or_none()

    async def list_paginated(
        self, skip: int, limit: int
    ) -> Tuple[List[Document], int]:
        total = await self.db.scalar(select(func.count()).select_from(Document))
        result = await self.db.execute(
            select(Document)
            .order_by(Document.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all()), int(total or 0)


class DocumentChunkRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def bulk_create(self, chunks: List[DocumentChunk]) -> List[DocumentChunk]:
        """Persist pre-built chunk rows (ids already assigned by the caller)."""
        if not chunks:
            return []
        self.db.add_all(chunks)
        await self.db.flush()
        return chunks
