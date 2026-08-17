"""LLM query rewriting for multi-turn retrieval.

Rewrites a context-dependent follow-up ("what about grad students?") into a
standalone question using the recent conversation, so the retriever receives a
self-contained query. Best-effort: empty history, a disabled flag, or any API
error falls back to the original query — rewriting must never break retrieval.
"""
from typing import List, Optional, Tuple

from app.core.config import settings
from app.llm.client import get_openai_client

_SYSTEM_PROMPT = (
    "You rewrite a user's latest question into a standalone search query using "
    "the conversation so far. Resolve pronouns and references to earlier turns "
    "(e.g. 'that policy', 'what about them'). If the question is already "
    "self-contained, return it unchanged. Return ONLY the rewritten question, "
    "with no preamble, explanation, or quotes."
)


class QueryRewriter:
    def __init__(self, model: Optional[str] = None):
        self._client = get_openai_client()
        self.model = model or settings.DEFAULT_LLM_MODEL

    async def rewrite(self, query: str, history: List[Tuple[str, str]]) -> str:
        """Return a standalone query. Falls back to ``query`` on no history/errors."""
        if not history:
            return query
        transcript = "\n".join(
            f"{role.capitalize()}: {content}" for role, content in history
        )
        user_message = (
            f"Conversation so far:\n{transcript}\n\n"
            f"Latest question: {query}\n\nStandalone question:"
        )
        try:
            response = await self._client.chat.completions.create(
                model=self.model,
                temperature=0.0,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
            )
            rewritten = (response.choices[0].message.content or "").strip()
            return rewritten or query
        except Exception:
            return query
