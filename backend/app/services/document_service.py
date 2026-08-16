"""Business logic for reading indexed documents."""
from typing import List, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge import Document
from app.repositories.document_repository import DocumentRepository


class DocumentService:
    def __init__(self, db: AsyncSession):
        self.repo = DocumentRepository(db)

    async def list_documents(
        self, page: int, page_size: int
    ) -> Tuple[List[Document], int]:
        skip = (page - 1) * page_size
        return await self.repo.list_paginated(skip=skip, limit=page_size)
