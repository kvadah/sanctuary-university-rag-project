"""Builds the admin analytics overview from persisted telemetry.

Aggregates usage, latency, token spend, feedback satisfaction, refusal rate, and
content/indexing counts for ``GET /analytics/overview``. Pure-column facts come from the
repositories' SQL aggregations; the per-answer ``meta_data`` JSON is reduced here in Python
(percentiles, token sums, refusal rate, per-day volume) so we avoid JSON-cast SQL and keep the
reduction unit-testable. The ``_`` module-level helpers are pure and covered by
``tests/test_analytics.py``.
"""
import datetime as dt
import math
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat import FeedbackRating
from app.repositories.analytics_repository import AnalyticsRepository
from app.repositories.document_repository import DocumentChunkRepository
from app.schemas.analytics import (
    AnalyticsOverview,
    ContentStats,
    IndexingStats,
    LatencyStats,
    QualityStats,
    TokenStats,
    UsageStats,
    VolumePoint,
)

# Upper bound on rows pulled from `messages` for in-Python reduction. Generous for a single
# institution; if a window ever exceeds it, stats reflect the most recent this-many answers.
_MESSAGE_CAP = 20000


class AnalyticsService:
    def __init__(self, db: AsyncSession):
        self._repo = AnalyticsRepository(db)
        self._chunks = DocumentChunkRepository(db)

    async def overview(self, days: int) -> AnalyticsOverview:
        since = _utcnow() - dt.timedelta(days=days)

        rows = await self._repo.assistant_messages_in_window(since, _MESSAGE_CAP)
        metas = [r.meta_data for r in rows if isinstance(r.meta_data, dict)]
        created = [r.created_at for r in rows]
        total_queries = len(rows)

        refusal_count = sum(1 for m in metas if m.get("retrieved_count") == 0)

        conversations = await self._repo.conversations_since(since)
        feedback = await self._repo.feedback_breakdown()
        jobs = await self._repo.indexing_jobs_by_status()
        documents, sources, active_sources, users = await self._repo.content_counts()
        chunks = await self._chunks.count_current()

        up = feedback.get(FeedbackRating.THUMBS_UP.value, 0)
        down = feedback.get(FeedbackRating.THUMBS_DOWN.value, 0)
        total_fb = up + down

        return AnalyticsOverview(
            window_days=days,
            usage=UsageStats(
                total_queries=total_queries,
                conversations=conversations,
                volume_by_day=[
                    VolumePoint(date=date, count=count)
                    for date, count in _volume_by_day(created, since)
                ],
            ),
            latency_ms=_latency_stats(metas),
            tokens=_token_stats(metas),
            quality=QualityStats(
                feedback_up=up,
                feedback_down=down,
                feedback_total=total_fb,
                up_ratio=(up / total_fb) if total_fb else None,
                refusal_count=refusal_count,
                refusal_rate=(refusal_count / total_queries) if total_queries else None,
            ),
            content=ContentStats(
                documents=documents,
                chunks=chunks,
                sources=sources,
                active_sources=active_sources,
                users=users,
            ),
            indexing=IndexingStats(by_status=jobs, total=sum(jobs.values())),
        )


# --- pure helpers (no DB; unit-tested in tests/test_analytics.py) ------------


def _utcnow() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _percentile(values: List[float], q: float) -> Optional[float]:
    """Nearest-rank percentile of ``values`` for ``q`` in [0, 100]; ``None`` if empty."""
    if not values:
        return None
    ordered = sorted(values)
    rank = math.ceil((q / 100.0) * len(ordered))  # 1-based rank
    idx = min(max(rank, 1), len(ordered)) - 1
    return float(ordered[idx])


def _latency_stats(metas: List[Dict[str, Any]]) -> LatencyStats:
    values = [
        float(m["latency_ms"])
        for m in metas
        if isinstance(m.get("latency_ms"), (int, float))
    ]
    if not values:
        return LatencyStats(sample_count=0)
    return LatencyStats(
        avg=round(sum(values) / len(values), 1),
        p50=_percentile(values, 50),
        p95=_percentile(values, 95),
        sample_count=len(values),
    )


def _token_stats(metas: List[Dict[str, Any]]) -> TokenStats:
    def total(key: str) -> int:
        # Skip None / missing — Gemini can omit usage on some responses.
        return sum(int(m[key]) for m in metas if isinstance(m.get(key), (int, float)))

    return TokenStats(
        prompt=total("prompt_tokens"),
        completion=total("completion_tokens"),
        total=total("total_tokens"),
    )


def _volume_by_day(
    created: List[dt.datetime], since: dt.datetime
) -> List[Tuple[str, int]]:
    """Count timestamps per UTC calendar day, gaps filled with zero.

    Returns ascending ``(iso_date, count)`` from ``since``'s day through today, so the chart
    has a continuous x-axis even on days with no queries.
    """
    counts: Dict[dt.date, int] = {}
    for ts in created:
        day = _as_utc_date(ts)
        counts[day] = counts.get(day, 0) + 1

    out: List[Tuple[str, int]] = []
    day = _as_utc_date(since)
    end = _utcnow().date()
    while day <= end:
        out.append((day.isoformat(), counts.get(day, 0)))
        day += dt.timedelta(days=1)
    return out


def _as_utc_date(ts: dt.datetime) -> dt.date:
    """Calendar date of ``ts`` in UTC (naive timestamps are treated as UTC)."""
    if ts.tzinfo is None:
        return ts.date()
    return ts.astimezone(dt.timezone.utc).date()
