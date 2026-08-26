"""Retrieval orchestration: hybrid dense + lexical search fused with RRF.

Runs dense vector search (Qdrant) and in-process BM25 lexical search over the
same RBAC/term-filtered corpus, fuses the two rankings with Reciprocal Rank
Fusion, then optionally rewrites the query for follow-ups (before retrieval) and
reranks the fused candidates with the LLM (after fusion). Both retrieval passes
honour the same ``allowed_classifications`` policy, so RBAC holds regardless of
which retriever surfaces a chunk.
"""
import logging
import time
from typing import Dict, List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.llm.embeddings import EmbeddingClient
from app.llm.query_rewriter import QueryRewriter
from app.models.knowledge import DocumentClassification
from app.models.user import User
from app.retrieval.bm25_index import bm25_index_cache
from app.retrieval.fusion import reciprocal_rank_fusion
from app.retrieval.rbac import allowed_classifications
from app.retrieval.reranker import LLMReranker
from app.retrieval.types import RetrievedChunk
from app.retrieval.vector_store import QdrantVectorStore

logger = logging.getLogger(__name__)


def _record(timings: Optional[Dict[str, float]], key: str, start: float) -> None:
    """Store elapsed ms since ``start`` under ``key`` (no-op when not profiling)."""
    if timings is not None:
        timings[key] = (time.perf_counter() - start) * 1000


class Retriever:
    def __init__(self, db: AsyncSession):
        self._db = db  # BM25 reads its corpus from Postgres; dense uses Qdrant
        self._embeddings = EmbeddingClient()
        self._store = QdrantVectorStore()

    async def retrieve(
        self,
        query: str,
        user: User,
        academic_term: Optional[str] = None,
        top_k: Optional[int] = None,
        history: Optional[List[Tuple[str, str]]] = None,
        timings: Optional[Dict[str, float]] = None,
    ) -> List[RetrievedChunk]:
        """Return the fused, RBAC-filtered chunks most relevant to ``query``.

        When ``timings`` is provided, per-stage elapsed ms (rewrite/embed/qdrant/
        bm25/rerank) are recorded into it for latency profiling — passing it does
        not change what is retrieved.
        """
        top_k = top_k or settings.RAG_TOP_K
        allowed = allowed_classifications(user.role)

        # Contextualise follow-ups into a standalone query before retrieving.
        retrieval_query = query
        if settings.RAG_QUERY_REWRITE_ENABLED and history:
            started = time.perf_counter()
            retrieval_query = await QueryRewriter().rewrite(query, history)
            _record(timings, "rewrite_ms", started)

        dense_hits = await self._dense(
            retrieval_query, allowed, academic_term, timings
        )

        started = time.perf_counter()
        bm25_hits = await self._bm25(retrieval_query, allowed, academic_term)
        _record(timings, "bm25_ms", started)

        fused = _fuse(dense_hits, bm25_hits)
        if not fused:
            result: List[RetrievedChunk] = []
        elif settings.RAG_RERANK_ENABLED and len(fused) > 1:
            started = time.perf_counter()
            result = await LLMReranker().rerank(retrieval_query, fused, top_k)
            _record(timings, "rerank_ms", started)
        else:
            result = fused[:top_k]

        if timings is not None:
            logger.info(
                "retrieve timing: %s",
                " ".join(f"{k[:-3]}={v:.0f}ms" for k, v in timings.items()),
            )
        return result

    async def _dense(
        self,
        query: str,
        allowed: List[DocumentClassification],
        academic_term: Optional[str],
        timings: Optional[Dict[str, float]] = None,
    ) -> List[RetrievedChunk]:
        started = time.perf_counter()
        vector = await self._embeddings.embed_query(query)
        _record(timings, "embed_ms", started)
        started = time.perf_counter()
        points = await self._store.search(
            vector=vector,
            top_k=settings.RAG_CANDIDATE_K,
            allowed_classifications=allowed,
            academic_term=academic_term,
        )
        _record(timings, "qdrant_ms", started)
        hits: List[RetrievedChunk] = []
        for rank, point in enumerate(points, start=1):
            payload = point.payload or {}
            hits.append(
                RetrievedChunk(
                    chunk_id=str(payload.get("chunk_id", point.id)),
                    document_id=str(payload.get("document_id", "")),
                    document_title=payload.get("document_title", "Document"),
                    content=payload.get("content", ""),
                    classification=payload.get("classification"),
                    academic_term=payload.get("academic_term"),
                    page_number=payload.get("page_number"),
                    section_title=payload.get("section_title"),
                    score=float(point.score),
                    dense_rank=rank,
                )
            )
        return hits

    async def _bm25(
        self,
        query: str,
        allowed: List[DocumentClassification],
        academic_term: Optional[str],
    ) -> List[RetrievedChunk]:
        index = await bm25_index_cache.get(self._db)
        return index.search(
            query,
            allowed_classifications=allowed,
            academic_term=academic_term,
            top_k=settings.RAG_CANDIDATE_K,
        )


def _fuse(
    dense_hits: List[RetrievedChunk], bm25_hits: List[RetrievedChunk]
) -> List[RetrievedChunk]:
    """Merge dense + lexical hits by ``chunk_id`` and order them by RRF score."""
    by_id: Dict[str, RetrievedChunk] = {}
    for hit in dense_hits:  # dense first: its payload is the canonical copy
        by_id.setdefault(hit.chunk_id, hit)
    for hit in bm25_hits:
        existing = by_id.get(hit.chunk_id)
        if existing is None:
            by_id[hit.chunk_id] = hit
        else:
            existing.bm25_rank = hit.bm25_rank  # annotate the shared chunk

    fused_scores = reciprocal_rank_fusion(
        [[h.chunk_id for h in dense_hits], [h.chunk_id for h in bm25_hits]]
    )
    ordered_ids = sorted(
        by_id, key=lambda cid: fused_scores.get(cid, 0.0), reverse=True
    )
    results: List[RetrievedChunk] = []
    for cid in ordered_ids:
        chunk = by_id[cid]
        chunk.score = fused_scores.get(cid, 0.0)
        results.append(chunk)
    return results
