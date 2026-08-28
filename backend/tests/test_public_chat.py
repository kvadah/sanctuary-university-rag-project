"""Anonymous ("guest") chat: scope, no-persistence, and open-endpoint checks.

Kept in the repo's synchronous, service-free testing style — async service
methods are driven with ``asyncio.run`` and every external collaborator
(retriever/generator/repositories) is mocked, so no Qdrant/Gemini/DB is needed.
"""
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.knowledge import DocumentClassification as DC
from app.retrieval.rbac import anonymous_classifications


def test_anonymous_scope_is_public_and_student():
    scope = anonymous_classifications()
    assert scope == [DC.PUBLIC, DC.STUDENT]
    # A guest must never reach a gated tier.
    assert DC.FACULTY not in scope
    assert DC.STAFF not in scope
    assert DC.ADMIN not in scope


def test_anonymous_scope_returns_a_copy():
    # Mutating the returned list must not corrupt the policy source of truth.
    anonymous_classifications().append(DC.ADMIN)
    assert anonymous_classifications() == [DC.PUBLIC, DC.STUDENT]


def test_answer_public_uses_anon_scope_and_never_persists():
    """The public path retrieves with PUBLIC+STUDENT and touches no repositories."""
    from app.schemas.chat import PublicChatQueryRequest, PublicChatQueryResponse

    with patch("app.services.rag_service.Retriever"), \
            patch("app.services.rag_service.AnswerGenerator"), \
            patch("app.services.rag_service.ConversationRepository"), \
            patch("app.services.rag_service.MessageRepository"):
        from app.services.rag_service import RagService

        service = RagService(db=MagicMock())
        service.retriever.retrieve = AsyncMock(return_value=[])
        service.generator.generate = AsyncMock(
            return_value={"answer": "Public answer.", "usage": {}}
        )

        req = PublicChatQueryRequest(query="library hours?", history=None)
        resp = asyncio.run(service.answer_public(req))

        assert resp.answer == "Public answer."
        # The public response schema exposes no conversation/message identifiers.
        assert set(PublicChatQueryResponse.model_fields.keys()) == {
            "answer",
            "citations",
            "meta",
        }

        # Retrieval was hard-scoped to the anonymous classifications.
        service.retriever.retrieve.assert_awaited_once()
        scope_arg = service.retriever.retrieve.await_args.args[1]
        assert scope_arg == [DC.PUBLIC, DC.STUDENT]

        # Nothing was persisted — no conversation created/touched, no message written.
        service.messages.create.assert_not_called()
        service.conversations.create.assert_not_called()
        service.conversations.touch.assert_not_called()


def test_public_history_is_capped_and_ordered():
    from app.core.config import settings
    from app.schemas.chat import PublicChatTurn
    from app.services.rag_service import _public_history

    n = settings.RAG_HISTORY_TURNS
    turns = [
        PublicChatTurn(role="user" if i % 2 == 0 else "assistant", content=f"m{i}")
        for i in range(n + 4)
    ]
    capped = _public_history(turns)

    assert len(capped) == n  # older turns dropped
    assert capped[-1] == (turns[-1].role, turns[-1].content)  # keeps most recent
    assert all(isinstance(t, tuple) and len(t) == 2 for t in capped)
    assert _public_history(None) == []


def test_public_query_endpoint_requires_no_auth_but_authed_route_still_protected():
    from fastapi.testclient import TestClient
    from app.core.db import get_db
    from app.main import app
    from app.schemas.chat import PublicChatQueryResponse

    class _StubRag:
        def __init__(self, db):
            pass

        async def answer_public(self, payload):
            return PublicChatQueryResponse(answer="hi", citations=[], meta={})

    async def _fake_db():
        yield None

    app.dependency_overrides[get_db] = _fake_db
    try:
        with patch("app.api.chat.RagService", _StubRag):
            client = TestClient(app)

            # No Authorization header at all -> the guest endpoint answers.
            resp = client.post("/api/v1/chat/public/query", json={"query": "hi"})
            assert resp.status_code == 200
            assert resp.json()["answer"] == "hi"

            # The authenticated route must remain closed to anonymous callers.
            authed = client.post("/api/v1/chat/query", json={"query": "hi"})
            assert authed.status_code in (401, 403)
    finally:
        app.dependency_overrides.pop(get_db, None)
