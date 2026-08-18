"""Shared LLM client factory (OpenAI-compatible).

Returns a single cached ``AsyncOpenAI`` instance, reused across requests. By
default it is pointed at Google Gemini's OpenAI-compatible endpoint (free tier);
set ``LLM_PROVIDER=openai`` in ``.env`` to use OpenAI proper instead. The active
provider's key and base URL come from :mod:`app.core.config`; a clear error is
raised if the key is missing so misconfiguration fails loudly rather than at the
API boundary.
"""
from functools import lru_cache

from openai import AsyncOpenAI

from app.core.config import settings


@lru_cache(maxsize=1)
def get_openai_client() -> AsyncOpenAI:
    if not settings.LLM_API_KEY:
        raise RuntimeError(
            f"No LLM API key configured for LLM_PROVIDER='{settings.LLM_PROVIDER}'. "
            "Set GEMINI_API_KEY (or OPENAI_API_KEY) in sanctuary-rag/.env to "
            "enable embeddings and answer generation."
        )
    return AsyncOpenAI(
        api_key=settings.LLM_API_KEY,
        base_url=settings.LLM_BASE_URL or None,
    )
