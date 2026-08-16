"""OpenAI embedding client.

Wraps the OpenAI embeddings endpoint with simple batching. Returns vectors in
the same order as the input texts.
"""
from typing import List, Optional

from app.core.config import settings
from app.llm.client import get_openai_client

# OpenAI accepts large batches, but we cap conservatively to stay well within
# per-request input limits.
_BATCH_SIZE = 100


class EmbeddingClient:
    def __init__(self, model: Optional[str] = None):
        self._client = get_openai_client()
        self.model = model or settings.DEFAULT_EMBEDDING_MODEL

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of texts, preserving order."""
        if not texts:
            return []

        vectors: List[List[float]] = []
        for start in range(0, len(texts), _BATCH_SIZE):
            batch = texts[start : start + _BATCH_SIZE]
            response = await self._client.embeddings.create(
                model=self.model, input=batch
            )
            ordered = sorted(response.data, key=lambda item: item.index)
            vectors.extend(item.embedding for item in ordered)
        return vectors

    async def embed_query(self, text: str) -> List[float]:
        """Embed a single query string."""
        vectors = await self.embed_texts([text])
        return vectors[0]
