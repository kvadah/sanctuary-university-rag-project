"""Unified retrieval hit shared across the dense, lexical, fusion, and rerank stages.

Both retrievers emit ``RetrievedChunk`` so fusion and reranking operate on one
shape, and :class:`~app.services.rag_service.RagService` builds citations from it
without caring which retriever a chunk came from.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class RetrievedChunk:
    chunk_id: str
    document_id: str
    document_title: str
    content: str
    classification: Optional[str] = None
    academic_term: Optional[str] = None
    page_number: Optional[int] = None
    section_title: Optional[str] = None
    score: float = 0.0
    # Original position in each retriever's ranking, kept for telemetry/debugging.
    dense_rank: Optional[int] = None
    bm25_rank: Optional[int] = None
