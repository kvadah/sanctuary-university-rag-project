"""RAG query orchestration: retrieve -> generate -> persist -> respond.

Retrieval is hybrid (dense + BM25 fused with RRF) with optional LLM query
rewriting and reranking; generation is grounded in the retrieved chunks and
carries recent conversation turns for multi-turn memory.
"""
import time
import uuid
from typing import Any, Dict, List, Tuple

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
        self.retriever = Retriever(db)
        self.generator = AnswerGenerator()

    async def answer_query(
        self, request: ChatQueryRequest, user: User
    ) -> ChatQueryResponse:
        conversation = await self._resolve_conversation(request, user)

        # Load prior turns BEFORE persisting the current question, so history
        # excludes this turn. Empty for a brand-new conversation.
        history = await self._recent_history(conversation.id)

        await self.messages.create(
            conversation_id=conversation.id,
            role=MessageRole.USER,
            content=request.query,
        )

        started = time.perf_counter()
        hits = await self.retriever.retrieve(
            request.query,
            user,
            academic_term=request.academic_term,
            history=history,
        )

        context_chunks: List[Dict[str, Any]] = []
        citations: List[Citation] = []
        for position, hit in enumerate(hits, start=1):
            context_chunks.append(
                {
                    "index": position,
                    "title": hit.document_title,
                    "page_number": hit.page_number,
                    "content": hit.content,
                }
            )
            citations.append(
                Citation(
                    index=position,
                    document_id=uuid.UUID(hit.document_id),
                    document_title=hit.document_title,
                    chunk_id=uuid.UUID(hit.chunk_id),
                    page_number=hit.page_number,
                    section_title=hit.section_title,
                    score=float(hit.score),
                    snippet=_snippet(hit.content),
                )
            )

        generated = await self.generator.generate(
            request.query, context_chunks, history=history
        )
        answer = generated["answer"]
        latency_ms = int((time.perf_counter() - started) * 1000)
        meta: Dict[str, Any] = {
            "model": settings.DEFAULT_LLM_MODEL,
            "latency_ms": latency_ms,
            "retrieved_count": len(hits),
            "retrieval_mode": "hybrid",
            "rerank_enabled": settings.RAG_RERANK_ENABLED,
            "query_rewritten": bool(settings.RAG_QUERY_REWRITE_ENABLED and history),
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

    async def _recent_history(
        self, conversation_id: uuid.UUID
    ) -> List[Tuple[str, str]]:
        """Recent (role, content) turns for query rewriting + generation memory."""
        messages = await self.messages.list_recent(
            conversation_id, settings.RAG_HISTORY_TURNS
        )
        # Message.role is stored as the MessageRole string value ("user"/"assistant").
        return [(m.role, m.content) for m in messages]


def _snippet(text: str) -> str:
    text = " ".join(text.split())
    return text if len(text) <= _SNIPPET_CHARS else text[:_SNIPPET_CHARS].rstrip() + "…"
