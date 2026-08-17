"""In-process BM25 lexical index over current document chunks.

Complements dense vector search with exact-term matching (course codes, policy
numbers, acronyms) that embeddings often miss. Postgres holds the chunk text, so
the index is built from there and cached per process, rebuilt when the count of
current chunks changes. RBAC and academic-term filtering are applied per query,
so one shared index serves every user.

Known limitation: the cache is per-process and keyed on chunk count, which suits
the current single-worker deployment. A multi-worker or high-write deployment
would want a shared index or Postgres full-text search instead of this.
"""
import asyncio
import re
from dataclasses import dataclass
from typing import List, Optional

from rank_bm25 import BM25Okapi
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge import DocumentClassification
from app.repositories.document_repository import DocumentChunkRepository
from app.retrieval.types import RetrievedChunk

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> List[str]:
    """Lowercase word/number tokenizer — no NLP dependency, deterministic."""
    return _TOKEN_RE.findall(text.lower())


@dataclass
class _ChunkRecord:
    chunk_id: str
    document_id: str
    document_title: str
    content: str
    classification: str
    academic_term: Optional[str]
    page_number: Optional[int]
    section_title: Optional[str]


class BM25Index:
    """A BM25Okapi index plus the chunk metadata needed to build citations."""

    def __init__(self, records: List[_ChunkRecord]):
        self._records = records
        self._bm25 = (
            BM25Okapi([_tokenize(r.content) for r in records]) if records else None
        )

    @property
    def size(self) -> int:
        return len(self._records)

    @classmethod
    def build_from_rows(cls, rows) -> "BM25Index":
        """Build from repository rows exposing chunk + parent-document fields."""
        records = [
            _ChunkRecord(
                chunk_id=str(r.chunk_id),
                document_id=str(r.document_id),
                document_title=r.document_title or "Document",
                content=r.content or "",
                classification=(
                    r.classification.value
                    if isinstance(r.classification, DocumentClassification)
                    else str(r.classification)
                ),
                academic_term=r.academic_term,
                page_number=r.page_number,
                section_title=r.section_title,
            )
            for r in rows
        ]
        return cls(records)

    def search(
        self,
        query: str,
        allowed_classifications: List[DocumentClassification],
        academic_term: Optional[str] = None,
        top_k: int = 20,
    ) -> List[RetrievedChunk]:
        """Return the top-k lexical matches the caller may access, best first."""
        if not self._bm25:
            return []
        tokens = _tokenize(query)
        if not tokens:
            return []

        allowed = {c.value for c in allowed_classifications}
        scores = self._bm25.get_scores(tokens)

        candidates = []
        for record, score in zip(self._records, scores):
            if score <= 0:  # no lexical overlap with the query
                continue
            if record.classification not in allowed:
                continue
            if academic_term and record.academic_term != academic_term:
                continue
            candidates.append((record, float(score)))

        candidates.sort(key=lambda pair: pair[1], reverse=True)
        return [
            RetrievedChunk(
                chunk_id=record.chunk_id,
                document_id=record.document_id,
                document_title=record.document_title,
                content=record.content,
                classification=record.classification,
                academic_term=record.academic_term,
                page_number=record.page_number,
                section_title=record.section_title,
                score=score,
                bm25_rank=rank,
            )
            for rank, (record, score) in enumerate(candidates[:top_k], start=1)
        ]


class BM25IndexCache:
    """Process-level cache of a :class:`BM25Index`, rebuilt when chunk count changes."""

    def __init__(self):
        self._index: Optional[BM25Index] = None
        self._token: Optional[int] = None
        self._lock = asyncio.Lock()

    async def get(self, db: AsyncSession) -> BM25Index:
        repo = DocumentChunkRepository(db)
        token = await repo.count_current()
        if self._index is not None and self._token == token:
            return self._index
        async with self._lock:
            # Re-check under the lock: another request may have just rebuilt it.
            if self._index is not None and self._token == token:
                return self._index
            rows = await repo.list_current_for_index()
            self._index = BM25Index.build_from_rows(rows)
            self._token = token
            return self._index


# Shared across requests in this process.
bm25_index_cache = BM25IndexCache()
