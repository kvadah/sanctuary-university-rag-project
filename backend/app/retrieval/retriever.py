"""Retrieval orchestration: embed the query, then RBAC-filtered vector search."""
from typing import List, Optional

from qdrant_client import models as qm

from app.core.config import settings
from app.llm.embeddings import EmbeddingClient
from app.models.user import User
from app.retrieval.rbac import allowed_classifications
from app.retrieval.vector_store import QdrantVectorStore


class Retriever:
    def __init__(self):
        self._embeddings = EmbeddingClient()
        self._store = QdrantVectorStore()

    async def retrieve(
        self,
        query: str,
        user: User,
        academic_term: Optional[str] = None,
        top_k: Optional[int] = None,
    ) -> List[qm.ScoredPoint]:
        """Return the chunks most relevant to ``query`` that ``user`` may access."""
        vector = await self._embeddings.embed_query(query)
        return await self._store.search(
            vector=vector,
            top_k=top_k or settings.RAG_TOP_K,
            allowed_classifications=allowed_classifications(user.role),
            academic_term=academic_term,
        )
