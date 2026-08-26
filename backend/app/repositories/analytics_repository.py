"""Aggregation queries for the admin analytics dashboard (DB access only).

Provides the read-side metrics for :class:`app.services.analytics_service.AnalyticsService`.
Pure-column facts (counts, group-bys) are aggregated here in SQL; the per-answer
``messages.meta_data`` JSON is returned raw and reduced in Python by the service, so we
avoid JSON-cast SQL and keep that reduction unit-testable.
"""
import datetime as dt
from typing import Dict, List, Tuple

from sqlalchemy import Row, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import IndexingJob
from app.models.chat import Conversation, Feedback, Message, MessageRole
from app.models.knowledge import Document, KnowledgeSource
from app.models.user import User


class AnalyticsRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def assistant_messages_in_window(
        self, since: dt.datetime, cap: int
    ) -> List[Row]:
        """``(created_at, meta_data)`` for assistant messages since ``since``, newest first.

        Capped at ``cap`` rows so a very large window cannot pull the whole table into
        memory; the service reduces the JSON telemetry (latency/tokens/refusals/volume).
        """
        result = await self.db.execute(
            select(Message.created_at, Message.meta_data)
            .where(
                Message.role == MessageRole.ASSISTANT.value,
                Message.created_at >= since,
            )
            .order_by(Message.created_at.desc())
            .limit(cap)
        )
        return list(result.all())

    async def conversations_since(self, since: dt.datetime) -> int:
        total = await self.db.scalar(
            select(func.count())
            .select_from(Conversation)
            .where(Conversation.created_at >= since)
        )
        return int(total or 0)

    async def feedback_breakdown(self) -> Dict[int, int]:
        """Feedback counts keyed by rating value (1 = thumbs up, -1 = thumbs down)."""
        result = await self.db.execute(
            select(Feedback.rating, func.count()).group_by(Feedback.rating)
        )
        return {int(rating): int(count) for rating, count in result.all()}

    async def indexing_jobs_by_status(self) -> Dict[str, int]:
        """Indexing-job counts keyed by status string (PENDING/PROCESSING/COMPLETED/FAILED)."""
        result = await self.db.execute(
            select(IndexingJob.status, func.count()).group_by(IndexingJob.status)
        )
        return {str(status): int(count) for status, count in result.all()}

    async def content_counts(self) -> Tuple[int, int, int, int]:
        """Content inventory as ``(documents, sources, active_sources, users)``.

        Current-chunk counting is delegated to
        :meth:`DocumentChunkRepository.count_current` by the service, so it is not repeated here.
        """
        documents = await self.db.scalar(
            select(func.count()).select_from(Document)
        )
        sources = await self.db.scalar(
            select(func.count()).select_from(KnowledgeSource)
        )
        active_sources = await self.db.scalar(
            select(func.count())
            .select_from(KnowledgeSource)
            .where(KnowledgeSource.is_active.is_(True))
        )
        users = await self.db.scalar(select(func.count()).select_from(User))
        return (
            int(documents or 0),
            int(sources or 0),
            int(active_sources or 0),
            int(users or 0),
        )
