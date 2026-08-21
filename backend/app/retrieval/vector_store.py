"""Qdrant vector store wrapper for document chunks.

Owns the collection lifecycle, chunk upserts, and RBAC/term-filtered search.
Qdrant point ids are the ``DocumentChunk`` UUIDs (stored back on the row as
``vector_id``), so a search hit maps directly to its Postgres row.
"""
from typing import Any, Dict, List, Optional

from qdrant_client import AsyncQdrantClient, models as qm

from app.core.config import settings
from app.models.knowledge import DocumentClassification


class QdrantVectorStore:
    def __init__(self):
        self._client = AsyncQdrantClient(
            host=settings.QDRANT_HOST,
            port=settings.QDRANT_PORT,
            api_key=settings.QDRANT_API_KEY or None,
        )
        self.collection = settings.QDRANT_COLLECTION

    async def _collection_exists(self) -> bool:
        existing = await self._client.get_collections()
        return self.collection in {c.name for c in existing.collections}

    async def ensure_collection(self) -> None:
        """Create the collection if it does not already exist."""
        if await self._collection_exists():
            return
        await self._client.create_collection(
            collection_name=self.collection,
            vectors_config=qm.VectorParams(
                size=settings.EMBEDDING_DIM, distance=qm.Distance.COSINE
            ),
        )

    async def upsert(self, points: List[Dict[str, Any]]) -> None:
        """Upsert points shaped as ``{"id", "vector", "payload"}``."""
        if not points:
            return
        await self._client.upsert(
            collection_name=self.collection,
            points=[
                qm.PointStruct(id=p["id"], vector=p["vector"], payload=p["payload"])
                for p in points
            ],
        )

    async def search(
        self,
        vector: List[float],
        top_k: int,
        allowed_classifications: List[DocumentClassification],
        academic_term: Optional[str] = None,
    ) -> List[qm.ScoredPoint]:
        """Return the top-k current chunks the caller is permitted to see."""
        # On a fresh system the collection is not created until the first
        # document is ingested. Treat a missing collection as "no matches" so a
        # query against an empty knowledge base degrades to an empty result set
        # instead of raising Qdrant's 404 — which, as an unhandled 500, would
        # bypass CORSMiddleware and surface in the browser as a CORS error.
        if not await self._collection_exists():
            return []
        must: List[qm.Condition] = [
            qm.FieldCondition(
                key="classification",
                match=qm.MatchAny(any=[c.value for c in allowed_classifications]),
            ),
            qm.FieldCondition(key="is_current", match=qm.MatchValue(value=True)),
        ]
        if academic_term:
            must.append(
                qm.FieldCondition(
                    key="academic_term", match=qm.MatchValue(value=academic_term)
                )
            )

        # qdrant-client >=1.10 removed ``.search()``; ``query_points`` is the
        # replacement and returns a QueryResponse whose ``.points`` is the
        # ``List[ScoredPoint]`` this method is documented to return.
        response = await self._client.query_points(
            collection_name=self.collection,
            query=vector,
            query_filter=qm.Filter(must=must),
            limit=top_k,
            with_payload=True,
        )
        return response.points
