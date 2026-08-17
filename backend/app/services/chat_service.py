"""Chat history and feedback orchestration.

Querying/answer generation lives in :mod:`app.services.rag_service`; this service
covers the read-side (listing conversations, fetching a conversation's history) and
recording thumbs up/down feedback on assistant messages.
"""
import uuid
from typing import List, Tuple

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat import Conversation, Feedback
from app.models.user import User
from app.repositories.chat_repository import (
    ConversationRepository,
    FeedbackRepository,
    MessageRepository,
)
from app.schemas.chat import FeedbackCreate

_VALID_RATINGS = (1, -1)


class ChatService:
    def __init__(self, db: AsyncSession):
        self.conversations = ConversationRepository(db)
        self.messages = MessageRepository(db)
        self.feedbacks = FeedbackRepository(db)

    async def list_conversations(
        self, user: User, page: int, page_size: int
    ) -> Tuple[List[Conversation], int]:
        skip = (page - 1) * page_size
        return await self.conversations.list_by_user(
            user.id, skip=skip, limit=page_size
        )

    async def get_conversation(
        self, conversation_id: uuid.UUID, user: User
    ) -> Conversation:
        conversation = await self.conversations.get_with_messages(
            conversation_id, user.id
        )
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found.",
            )
        conversation.messages.sort(key=lambda m: m.created_at)
        return conversation

    async def submit_feedback(self, payload: FeedbackCreate, user: User) -> Feedback:
        if payload.rating not in _VALID_RATINGS:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="rating must be 1 (thumbs up) or -1 (thumbs down).",
            )
        message = await self.messages.get_owned(payload.message_id, user.id)
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found.",
            )
        return await self.feedbacks.upsert(
            message_id=payload.message_id,
            user_id=user.id,
            rating=payload.rating,
            comment=payload.comment,
        )
