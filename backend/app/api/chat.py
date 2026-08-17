"""Chat / RAG query, conversation history, and feedback endpoints."""
import math
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.chat import (
    ChatQueryRequest,
    ChatQueryResponse,
    ConversationListResponse,
    ConversationRead,
    FeedbackCreate,
    FeedbackRead,
)
from app.schemas.common import PaginationMeta
from app.services.chat_service import ChatService
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


@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List the current user's conversations, most recently updated first."""
    service = ChatService(db)
    items, total = await service.list_conversations(
        user, page=page, page_size=page_size
    )
    return ConversationListResponse(
        items=items,
        pagination=PaginationMeta(
            page=page,
            page_size=page_size,
            total_items=total,
            total_pages=math.ceil(total / page_size) if total else 0,
        ),
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationRead)
async def get_conversation(
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Fetch a single conversation with its full message history."""
    service = ChatService(db)
    return await service.get_conversation(conversation_id, user)


@router.post("/feedback", response_model=FeedbackRead)
async def submit_feedback(
    payload: FeedbackCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Record thumbs up/down feedback on an assistant message."""
    service = ChatService(db)
    return await service.submit_feedback(payload, user)
