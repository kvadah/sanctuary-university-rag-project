"""Admin analytics / observability endpoints."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import require_roles
from app.models.user import User, UserRole
from app.schemas.analytics import AnalyticsOverview
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])

# Observability is an admin-only view over everyone's usage.
AdminOnly = require_roles([UserRole.ADMIN])


@router.get("/overview", response_model=AnalyticsOverview)
async def analytics_overview(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(AdminOnly),
):
    """Aggregate usage, latency, token, quality, and content metrics for the given window."""
    service = AnalyticsService(db)
    return await service.overview(days)
