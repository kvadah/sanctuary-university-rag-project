import uuid
from typing import List, Tuple
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.knowledge_repository import KnowledgeSourceRepository
from app.schemas.knowledge import KnowledgeSourceCreate, KnowledgeSourceUpdate
from app.models.knowledge import KnowledgeSource


class KnowledgeService:
    """Business logic for managing knowledge sources."""

    def __init__(self, db: AsyncSession):
        self.repo = KnowledgeSourceRepository(db)

    async def create_source(self, data: KnowledgeSourceCreate) -> KnowledgeSource:
        return await self.repo.create(data)

    async def get_source(self, source_id: uuid.UUID) -> KnowledgeSource:
        source = await self.repo.get_by_id(source_id)
        if not source:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Knowledge source not found.",
            )
        return source

    async def list_sources(self, page: int, page_size: int) -> Tuple[List[KnowledgeSource], int]:
        skip = (page - 1) * page_size
        return await self.repo.list_paginated(skip=skip, limit=page_size)

    async def update_source(self, source_id: uuid.UUID, data: KnowledgeSourceUpdate) -> KnowledgeSource:
        source = await self.get_source(source_id)
        return await self.repo.update(source, data)

    async def delete_source(self, source_id: uuid.UUID) -> None:
        source = await self.get_source(source_id)
        await self.repo.delete(source)
