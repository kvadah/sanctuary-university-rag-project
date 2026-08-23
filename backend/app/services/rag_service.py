"""RAG query orchestration: retrieve -> generate -> persist -> respond.

Retrieval is hybrid (dense + BM25 fused with RRF) with optional LLM query
rewriting and reranking; generation is grounded in the retrieved chunks and
carries recent conversation turns for multi-turn memory. Two entry points share
the same retrieval/persistence path: ``answer_query`` returns a full response,
while ``prepare_stream`` + ``stream_answer`` stream the generation as SSE events.
"""
import logging
import time
import uuid
from dataclasses import dataclass
from typing import Any, AsyncIterator, Dict, List, Tuple

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

logger = logging.getLogger(__name__)

_SNIPPET_CHARS = 240


@dataclass
class QueryPrep:
    """Everything needed to generate an answer, gathered before generation.

    Produced by :meth:`RagService._prepare` and reused by both the full-response
    and streaming paths. Building this can raise a normal ``HTTPException`` (e.g.
    404), so a streaming endpoint should call it *before* opening the SSE stream.
    """

    conversation: Any
    history: List[Tuple[str, str]]
    context_chunks: List[Dict[str, Any]]
    citations: List[Citation]
    started: float


class RagService:
    def __init__(self, db: AsyncSession):
        self.conversations = ConversationRepository(db)
        self.messages = MessageRepository(db)
        self.retriever = Retriever(db)
        self.generator = AnswerGenerator()

    async def answer_query(
        self, request: ChatQueryRequest, user: User
    ) -> ChatQueryResponse:
        prep = await self._prepare(request, user)
        generated = await self.generator.generate(
            request.query, prep.context_chunks, history=prep.history
        )
        answer = generated["answer"]
        meta = self._build_meta(prep, generated.get("usage"))
        assistant_message = await self._persist_assistant(prep, answer, meta)

        return ChatQueryResponse(
            conversation_id=prep.conversation.id,
            message_id=assistant_message.id,
            answer=answer,
            citations=prep.citations,
            meta=meta,
        )

    async def prepare_stream(
        self, request: ChatQueryRequest, user: User
    ) -> QueryPrep:
        """Resolve/persist/retrieve before streaming so failures return a clean
        HTTP status (with CORS headers) rather than a broken event stream."""
        return await self._prepare(request, user)

    async def stream_answer(
        self, prep: QueryPrep, request: ChatQueryRequest
    ) -> AsyncIterator[Dict[str, Any]]:
        """Stream the answer for an already-prepared query as event dicts.

        Emits ``meta`` (conversation id + citations) first, then a ``delta`` per
        text chunk, then ``done`` (persisted message id + telemetry). A failure
        mid-generation becomes an ``error`` event — the HTTP response has already
        started, so it cannot change status.
        """
        yield {
            "type": "meta",
            "conversation_id": str(prep.conversation.id),
            "citations": [c.model_dump(mode="json") for c in prep.citations],
        }

        parts: List[str] = []
        usage: Dict[str, Any] = {}
        try:
            async for ev in self.generator.generate_stream(
                request.query, prep.context_chunks, history=prep.history
            ):
                if "delta" in ev:
                    parts.append(ev["delta"])
                    yield {"type": "delta", "text": ev["delta"]}
                elif "usage" in ev:
                    usage = ev["usage"] or {}

            answer = "".join(parts)
            meta = self._build_meta(prep, usage)
            assistant_message = await self._persist_assistant(prep, answer, meta)
            yield {
                "type": "done",
                "message_id": str(assistant_message.id),
                "meta": meta,
            }
        except Exception:  # noqa: BLE001 - surface to the client as a stream event
            logger.exception("Streaming generation failed")
            yield {
                "type": "error",
                "detail": "Failed to generate a response. Please try again.",
            }

    async def _prepare(
        self, request: ChatQueryRequest, user: User
    ) -> QueryPrep:
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

        return QueryPrep(
            conversation=conversation,
            history=history,
            context_chunks=context_chunks,
            citations=citations,
            started=started,
        )

    def _build_meta(
        self, prep: QueryPrep, usage: Dict[str, Any] | None
    ) -> Dict[str, Any]:
        return {
            "model": settings.DEFAULT_LLM_MODEL,
            "latency_ms": int((time.perf_counter() - prep.started) * 1000),
            "retrieved_count": len(prep.context_chunks),
            "retrieval_mode": "hybrid",
            "rerank_enabled": settings.RAG_RERANK_ENABLED,
            "query_rewritten": bool(
                settings.RAG_QUERY_REWRITE_ENABLED and prep.history
            ),
            **(usage or {}),
        }

    async def _persist_assistant(
        self, prep: QueryPrep, answer: str, meta: Dict[str, Any]
    ):
        citation_payload = [c.model_dump(mode="json") for c in prep.citations]
        return await self.messages.create(
            conversation_id=prep.conversation.id,
            role=MessageRole.ASSISTANT,
            content=answer,
            citations={"items": citation_payload} if citation_payload else None,
            meta_data=meta,
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
