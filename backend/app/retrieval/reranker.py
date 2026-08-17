"""LLM-based reranking of fused retrieval candidates.

Reorders candidate chunks by relevance to the query using the chat model, which
keeps us free of a heavy local cross-encoder dependency (the project is
"API-based, no heavy local ML deps"). Best-effort: any API or parsing failure
falls back to the incoming fusion order, so reranking never breaks the answer.
"""
import json
import re
from typing import List, Optional

from app.core.config import settings
from app.llm.client import get_openai_client
from app.retrieval.types import RetrievedChunk

_SYSTEM_PROMPT = (
    "You are a search reranker. Given a question and a numbered list of passages, "
    "decide which passages are most relevant to answering the question. Respond "
    "with ONLY a JSON array of passage numbers ordered most-relevant first, e.g. "
    "[3, 1, 5]. Include only genuinely relevant passages; omit irrelevant ones."
)

_SNIPPET_CHARS = 500


class LLMReranker:
    def __init__(self, model: Optional[str] = None):
        self._client = get_openai_client()
        self.model = model or settings.DEFAULT_LLM_MODEL

    async def rerank(
        self, query: str, candidates: List[RetrievedChunk], top_k: int
    ) -> List[RetrievedChunk]:
        """Return the ``top_k`` most relevant candidates; fusion order on failure."""
        if len(candidates) <= 1:
            return candidates[:top_k]

        listing = "\n".join(
            f"[{i}] {c.document_title}: {c.content[:_SNIPPET_CHARS]}"
            for i, c in enumerate(candidates, start=1)
        )
        user_message = f"Question: {query}\n\nPassages:\n{listing}"
        try:
            response = await self._client.chat.completions.create(
                model=self.model,
                temperature=0.0,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
            )
            order = _parse_order(response.choices[0].message.content or "", len(candidates))
        except Exception:
            order = []

        if not order:
            return candidates[:top_k]

        ranked = [candidates[i - 1] for i in order]
        return ranked[:top_k]


def _parse_order(raw: str, n: int) -> List[int]:
    """Extract 1-based indices within [1, n] from the model's JSON array reply."""
    match = re.search(r"\[[^\]]*\]", raw)
    if not match:
        return []
    try:
        parsed = json.loads(match.group(0))
    except (ValueError, TypeError):
        return []
    seen = set()
    order: List[int] = []
    for value in parsed:
        if isinstance(value, int) and 1 <= value <= n and value not in seen:
            seen.add(value)
            order.append(value)
    return order
