"""Chat / RAG query, conversation history, and feedback endpoints."""
import json
import math
import uuid

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import AsyncSessionLocal, get_db
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


@router.post("/query/stream")
async def query_stream(
    payload: ChatQueryRequest,
    user: User = Depends(get_current_user),
):
    """Streaming counterpart of ``/query``: emits Server-Sent Events.

    Retrieval and conversation resolution run before the stream opens, so bad
    input (e.g. an unknown conversation) still yields a proper HTTP error with
    CORS headers. Once streaming starts, each event is a ``data:`` line carrying
    JSON with a ``type`` of ``meta`` | ``delta`` | ``done`` | ``error``; the
    stream ends with ``data: [DONE]``.

    Note the session is managed by hand rather than via ``Depends(get_db)``: a
    ``StreamingResponse`` body is produced *after* FastAPI tears down ``yield``
    dependencies, so a dependency-provided session would already be committed and
    closed by the time we persist the assistant message mid-stream. We instead
    keep one session open for the whole request and commit once, after the answer
    is fully generated and persisted — so the user and assistant rows land atomically.
    """
    session = AsyncSessionLocal()
    try:
        service = RagService(session)
        prep = await service.prepare_stream(payload, user)
    except BaseException:
        # prepare_stream may raise a clean HTTPException (e.g. 404) before the
        # stream opens; roll back and close so we don't leak the session.
        await session.rollback()
        await session.close()
        raise

    async def events():
        try:
            async for event in service.stream_answer(prep, payload):
                # Commit BEFORE telling the client we're done: its onDone handler
                # refetches the conversation immediately, so the user+assistant
                # rows must be durably committed first or the refetch races the
                # commit and misses the new turn.
                if event.get("type") == "done":
                    await session.commit()
                yield f"data: {json.dumps(event)}\n\n"
            # Error path persists only the user row (no assistant message); commit
            # it here. No-op when 'done' already committed above.
            await session.commit()
            yield "data: [DONE]\n\n"
        except BaseException:
            # Includes client disconnects (CancelledError). stream_answer already
            # turns generation failures into an in-stream ``error`` event, so this
            # only guards the commit and the transport itself.
            await session.rollback()
            raise
        finally:
            await session.close()

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


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
