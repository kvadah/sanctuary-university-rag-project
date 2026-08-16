import uuid
from typing import Optional, List, Tuple
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.knowledge import KnowledgeSource, KnowledgeSourceType
from app.schemas.knowledge import KnowledgeSourceCreate, KnowledgeSourceUpdate


class KnowledgeSourceRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: KnowledgeSourceCreate) -> KnowledgeSource:
        """Persist a new knowledge source."""
        source = KnowledgeSource(
            name=data.name,
            description=data.description,
            source_type=data.source_type,
            config=data.config,
            is_active=True,
        )
        self.db.add(source)
        await self.db.flush()
        await self.db.refresh(source)
        return source

    async def get_by_id(self, source_id: uuid.UUID) -> Optional[KnowledgeSource]:
        """Fetch a knowledge source by primary key."""
        result = await self.db.execute(
            select(KnowledgeSource).where(KnowledgeSource.id == source_id)
        )
        return result.scalar_one_or_none()

    async def list_paginated(self, skip: int, limit: int) -> Tuple[List[KnowledgeSource], int]:
        """Return a page of sources (newest first) together with the total count."""
        total = await self.db.scalar(select(func.count()).select_from(KnowledgeSource))
        result = await self.db.execute(
            select(KnowledgeSource)
            .order_by(KnowledgeSource.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all()), int(total or 0)

    async def update(self, source: KnowledgeSource, data: KnowledgeSourceUpdate) -> KnowledgeSource:
        """Apply a partial update to an existing source."""
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(source, field, value)
        await self.db.flush()
        await self.db.refresh(source)
        return source

    async def delete(self, source: KnowledgeSource) -> None:
        """Remove a source (cascades to its documents)."""
        await self.db.delete(source)
        await self.db.flush()

    async def get_or_create_upload_source(
        self, source_type: KnowledgeSourceType
    ) -> KnowledgeSource:
        """Return a shared KnowledgeSource for uploaded files of ``source_type``.

        Uploaded documents are grouped under one auto-created source per type,
        so ad-hoc uploads still satisfy the Document -> KnowledgeSource FK.
        """
        name = f"Uploaded {source_type.value} Documents"
        result = await self.db.execute(
            select(KnowledgeSource).where(KnowledgeSource.name == name)
        )
        source = result.scalar_one_or_none()
        if source:
            return source

        source = KnowledgeSource(
            name=name,
            description="Auto-created container for uploaded documents.",
            source_type=source_type,
            is_active=True,
        )
        self.db.add(source)
        await self.db.flush()
        await self.db.refresh(source)
        return source
