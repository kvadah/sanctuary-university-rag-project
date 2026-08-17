"""Reciprocal Rank Fusion for combining ranked retrieval result lists.

RRF merges several independently-ranked lists (here: dense vector search and
BM25 lexical search) into one ranking using only positions, so the two score
scales never have to be reconciled. Pure functions, unit-testable without any
services.
"""
from typing import Dict, List, Optional

from app.core.config import settings


def reciprocal_rank_fusion(
    ranked_lists: List[List[str]], k: Optional[int] = None
) -> Dict[str, float]:
    """Fuse ranked id lists into an ``id -> RRF score`` map (higher is better).

    Each input list is ordered best-first. An id's score is the sum, over every
    list it appears in, of ``1 / (k + rank)`` where ``rank`` is 1-based. Larger
    ``k`` compresses the influence of rank differences.
    """
    if k is None:
        k = settings.RAG_RRF_K
    scores: Dict[str, float] = {}
    for ranked in ranked_lists:
        for rank, item_id in enumerate(ranked, start=1):
            scores[item_id] = scores.get(item_id, 0.0) + 1.0 / (k + rank)
    return scores


def fuse_ranked_ids(
    ranked_lists: List[List[str]], k: Optional[int] = None
) -> List[str]:
    """Return the fused ids ordered by RRF score, best first."""
    scores = reciprocal_rank_fusion(ranked_lists, k)
    return sorted(scores, key=lambda item_id: scores[item_id], reverse=True)
