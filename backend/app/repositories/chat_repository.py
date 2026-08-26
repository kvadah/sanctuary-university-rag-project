"""Repositories for chat conversations, messages, and feedback (DB access only)."""
import uuid
from typing import List, Optional, Tuple

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.chat import Conversation, Feedback, Message, MessageRole


class ConversationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self, user_id: uuid.UUID, title: str = "New Conversation"
    ) -> Conversation:
        conversation = Conversation(user_id=user_id, title=title)
        self.db.add(conversation)
        await self.db.flush()
        await self.db.refresh(conversation)
        return conversation

    async def get_owned(
        self, conversation_id: uuid.UUID, user_id: uuid.UUID
    ) -> Optional[Conversation]:
        """Fetch a conversation only if it belongs to ``user_id``."""
        result = await self.db.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def touch(self, conversation_id: uuid.UUID) -> None:
        """Bump ``updated_at`` so the conversation sorts as most-recently engaged.

        Adding a message only inserts a child row, which does not fire the parent's
        ``onupdate``; this explicit update keeps the "recently active" ordering in
        :meth:`list_by_user` accurate. Uses ``func.now()`` for server-side time,
        matching how the column is otherwise set.
        """
        await self.db.execute(
            update(Conversation)
            .where(Conversation.id == conversation_id)
            .values(updated_at=func.now())
        )

    async def list_by_user(
        self, user_id: uuid.UUID, skip: int, limit: int
    ) -> Tuple[List[Conversation], int]:
        """Return a page of the user's conversations, most recently updated first."""
        total = await self.db.scalar(
            select(func.count())
            .select_from(Conversation)
            .where(Conversation.user_id == user_id)
        )
        result = await self.db.execute(
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all()), int(total or 0)

    async def get_with_messages(
        self, conversation_id: uuid.UUID, user_id: uuid.UUID
    ) -> Optional[Conversation]:
        """Fetch an owned conversation with its messages eagerly loaded."""
        result = await self.db.execute(
            select(Conversation)
            .options(selectinload(Conversation.messages))
            .where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()


class MessageRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        *,
        conversation_id: uuid.UUID,
        role: MessageRole,
        content: str,
        citations: Optional[dict] = None,
        meta_data: Optional[dict] = None,
    ) -> Message:
        message = Message(
            conversation_id=conversation_id,
            role=role.value if isinstance(role, MessageRole) else role,
            content=content,
            citations=citations,
            meta_data=meta_data,
        )
        self.db.add(message)
        await self.db.flush()
        await self.db.refresh(message)
        return message

    async def get_owned(
        self, message_id: uuid.UUID, user_id: uuid.UUID
    ) -> Optional[Message]:
        """Fetch a message only if its conversation belongs to ``user_id``."""
        result = await self.db.execute(
            select(Message)
            .join(Conversation, Message.conversation_id == Conversation.id)
            .where(
                Message.id == message_id,
                Conversation.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_recent(
        self, conversation_id: uuid.UUID, limit: int
    ) -> List[Message]:
        """Return up to ``limit`` most recent messages, in chronological order."""
        result = await self.db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        messages = list(result.scalars().all())
        messages.reverse()  # oldest-first for prompt construction
        return messages


class FeedbackRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def upsert(
        self,
        *,
        message_id: uuid.UUID,
        user_id: uuid.UUID,
        rating: int,
        comment: Optional[str] = None,
    ) -> Feedback:
        """Create feedback for (message, user), or update it if it already exists."""
        result = await self.db.execute(
            select(Feedback).where(
                Feedback.message_id == message_id,
                Feedback.user_id == user_id,
            )
        )
        feedback = result.scalar_one_or_none()
        if feedback is None:
            feedback = Feedback(
                message_id=message_id,
                user_id=user_id,
                rating=rating,
                comment=comment,
            )
            self.db.add(feedback)
        else:
            feedback.rating = rating
            feedback.comment = comment
        await self.db.flush()
        await self.db.refresh(feedback)
        return feedback
