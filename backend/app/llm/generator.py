"""Grounded answer generation over retrieved context.

Builds a citation-friendly prompt from numbered context blocks and calls the
OpenAI chat-completions endpoint. The model is instructed to answer only from the
provided context and to cite sources as ``[n]``; if the context is empty we
short-circuit with a canned refusal and skip the API call.
"""
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.llm.client import get_openai_client

_SYSTEM_PROMPT = (
    "You are KnowledgeHub AI, an assistant for Sanctuary University. "
    "Answer the user's question using ONLY the numbered context passages provided. "
    "Cite the passages you use inline with their bracketed number, e.g. [1] or [2]. "
    "If the answer is not contained in the context, say you don't have that "
    "information in the available documents. Do not invent facts or cite passages "
    "that were not provided."
)

_NO_CONTEXT_ANSWER = (
    "I don't have any information about that in the documents available to you."
)


class AnswerGenerator:
    def __init__(self, model: Optional[str] = None):
        self._client = get_openai_client()
        self.model = model or settings.DEFAULT_LLM_MODEL

    async def generate(
        self, query: str, context_chunks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate an answer. ``context_chunks`` items carry index/title/page/content."""
        if not context_chunks:
            return {"answer": _NO_CONTEXT_ANSWER, "usage": {}}

        context = "\n\n".join(_format_block(c) for c in context_chunks)
        user_message = f"Context:\n{context}\n\nQuestion: {query}"

        response = await self._client.chat.completions.create(
            model=self.model,
            temperature=0.1,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
        )
        usage = response.usage
        return {
            "answer": response.choices[0].message.content or "",
            "usage": {
                "prompt_tokens": getattr(usage, "prompt_tokens", None),
                "completion_tokens": getattr(usage, "completion_tokens", None),
                "total_tokens": getattr(usage, "total_tokens", None),
            },
        }


def _format_block(chunk: Dict[str, Any]) -> str:
    header = f"[{chunk['index']}] {chunk.get('title', 'Document')}"
    page = chunk.get("page_number")
    if page:
        header += f" (p.{page})"
    return f"{header}:\n{chunk.get('content', '')}"
