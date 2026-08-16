"""Shared OpenAI async client factory.

A single cached ``AsyncOpenAI`` instance is reused across requests. The key is
read from ``settings.OPENAI_API_KEY``; a clear error is raised if it is missing
so misconfiguration fails loudly rather than at the API boundary.
"""
from functools import lru_cache

from openai import AsyncOpenAI

from app.core.config import settings


@lru_cache(maxsize=1)
def get_openai_client() -> AsyncOpenAI:
    if not settings.OPENAI_API_KEY:
        raise RuntimeError(
            "OPENAI_API_KEY is not configured. Set it in sanctuary-rag/.env to "
            "enable embeddings and answer generation."
        )
    return AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
