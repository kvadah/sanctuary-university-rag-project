"""RAG query orchestration: retrieve -> generate -> persist -> respond."""
import time
import uuid
from typing import Any, Dict, List

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.llm.generator import AnswerGenerator
from app.models.chat import MessageRole
from app.models.user import User
from app.repositories.chat_repository import (
    ConversationRepository,
    MessageRepository,
)
from app.retrieval.retriever import Retriever
from app.schemas.chat import ChatQueryRequest, ChatQueryResponse, Citation

_SNIPPET_CHARS = 240


class RagService:
    def __init__(self, db: AsyncSession):
        self.conversations = ConversationRepository(db)
        self.messages = MessageRepository(db)
        self.retriever = Retriever()
        self.generator = AnswerGenerator()

    async def answer_query(
        self, request: ChatQueryRequest, user: User
    ) -> ChatQueryResponse:
        conversation = await self._resolve_conversation(request, user)
        await self.messages.create(
            conversation_id=conversation.id,
            role=MessageRole.USER,
            content=request.query,
        )

        started = time.perf_counter()
        hits = await self.retriever.retrieve(
            request.query, user, academic_term=request.academic_term
        )

        context_chunks: List[Dict[str, Any]] = []
        citations: List[Citation] = []
        for position, hit in enumerate(hits, start=1):
            payload = hit.payload or {}
            content = payload.get("content", "")
            context_chunks.append(
                {
                    "index": position,
                    "title": payload.get("document_title", "Document"),
                    "page_number": payload.get("page_number"),
                    "content": content,
                }
            )
            citations.append(
                Citation(
                    index=position,
                    document_id=uuid.UUID(payload["document_id"]),
                    document_title=payload.get("document_title", "Document"),
                    chunk_id=uuid.UUID(payload["chunk_id"]),
                    page_number=payload.get("page_number"),
                    section_title=payload.get("section_title"),
                    score=float(hit.score),
                    snippet=_snippet(content),
                )
            )

        generated = await self.generator.generate(request.query, context_chunks)
        answer = generated["answer"]
        latency_ms = int((time.perf_counter() - started) * 1000)
        meta: Dict[str, Any] = {
            "model": settings.DEFAULT_LLM_MODEL,
            "latency_ms": latency_ms,
            "retrieved_count": len(hits),
            **(generated.get("usage") or {}),
        }

        citation_payload = [c.model_dump(mode="json") for c in citations]
        assistant_message = await self.messages.create(
            conversation_id=conversation.id,
            role=MessageRole.ASSISTANT,
            content=answer,
            citations={"items": citation_payload} if citation_payload else None,
            meta_data=meta,
        )

        return ChatQueryResponse(
            conversation_id=conversation.id,
            message_id=assistant_message.id,
            answer=answer,
            citations=citations,
            meta=meta,
        )

    async def _resolve_conversation(self, request: ChatQueryRequest, user: User):
        if request.conversation_id:
            conversation = await self.conversations.get_owned(
                request.conversation_id, user.id
            )
            if not conversation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Conversation not found.",
                )
            return conversation
        title = request.query.strip()[:60] or "New Conversation"
        return await self.conversations.create(user_id=user.id, title=title)


def _snippet(text: str) -> str:
    text = " ".join(text.split())
    return text if len(text) <= _SNIPPET_CHARS else text[:_SNIPPET_CHARS].rstrip() + "…"
