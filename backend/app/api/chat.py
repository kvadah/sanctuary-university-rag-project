"""Chat / RAG query endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.chat import ChatQueryRequest, ChatQueryResponse
from app.services.rag_service import RagService

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/query", response_model=ChatQueryResponse)
async def query(
    payload: ChatQueryRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Ask a question; retrieves RBAC-filtered context and returns a cited answer."""
    service = RagService(db)
    return await service.answer_query(payload, user)
