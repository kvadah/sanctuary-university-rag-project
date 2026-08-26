"""Response schemas for the admin analytics dashboard.

These are read models assembled by
:class:`app.services.analytics_service.AnalyticsService` from aggregated telemetry —
they are not backed by a single ORM row, so (unlike most schemas here) there is no
``from_attributes`` config.
"""
from typing import Dict, List, Optional

from pydantic import BaseModel


class VolumePoint(BaseModel):
    date: str  # ISO calendar date in UTC, e.g. "2026-08-26"
    count: int


class UsageStats(BaseModel):
    total_queries: int
    conversations: int
    volume_by_day: List[VolumePoint] = []


class LatencyStats(BaseModel):
    """Answer latency in milliseconds, over answers that recorded a value."""

    avg: Optional[float] = None
    p50: Optional[float] = None
    p95: Optional[float] = None
    sample_count: int = 0


class TokenStats(BaseModel):
    prompt: int = 0
    completion: int = 0
    total: int = 0


class QualityStats(BaseModel):
    feedback_up: int = 0
    feedback_down: int = 0
    feedback_total: int = 0
    up_ratio: Optional[float] = None  # None until any feedback exists
    refusal_count: int = 0
    refusal_rate: Optional[float] = None  # None when there were no queries


class ContentStats(BaseModel):
    documents: int = 0
    chunks: int = 0
    sources: int = 0
    active_sources: int = 0
    users: int = 0


class IndexingStats(BaseModel):
    by_status: Dict[str, int] = {}
    total: int = 0


class AnalyticsOverview(BaseModel):
    """Everything the admin dashboard needs in one payload (see GET /analytics/overview)."""

    window_days: int
    usage: UsageStats
    latency_ms: LatencyStats
    tokens: TokenStats
    quality: QualityStats
    content: ContentStats
    indexing: IndexingStats
