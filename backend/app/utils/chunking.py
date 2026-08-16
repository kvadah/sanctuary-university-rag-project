"""Token-based text chunking for the RAG ingestion pipeline.

Pure functions (no I/O, no services) so they can be unit-tested directly.
Token counts use ``tiktoken`` with the stable ``cl100k_base`` encoding — exact
model alignment is unnecessary for chunk sizing, and this encoding is always
available offline.
"""
from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

import tiktoken

# ``cl100k_base`` is bundled with tiktoken and needs no network access.
_ENCODING = tiktoken.get_encoding("cl100k_base")

# A parsed page: (page_number | None, text). DOCX/TXT have no pages -> None.
Page = Tuple[Optional[int], str]


@dataclass
class Chunk:
    """A single embeddable unit of a document."""

    chunk_index: int
    content: str
    token_count: int
    page_number: Optional[int] = None
    section_title: Optional[str] = None


def count_tokens(text: str) -> int:
    """Return the number of tokens in ``text``."""
    return len(_ENCODING.encode(text))


def chunk_pages(
    pages: Sequence[Page],
    max_tokens: int,
    overlap: int,
) -> List[Chunk]:
    """Split parsed pages into overlapping token windows.

    Chunks never span pages (so a chunk's ``page_number`` is meaningful for
    citations). ``chunk_index`` is assigned globally across the document.
    """
    if max_tokens <= 0:
        raise ValueError("max_tokens must be positive")
    if overlap < 0 or overlap >= max_tokens:
        raise ValueError("overlap must be >= 0 and < max_tokens")

    step = max_tokens - overlap
    chunks: List[Chunk] = []
    index = 0

    for page_number, text in pages:
        if not text or not text.strip():
            continue
        tokens = _ENCODING.encode(text)
        start = 0
        while start < len(tokens):
            window = tokens[start : start + max_tokens]
            content = _ENCODING.decode(window).strip()
            if content:
                chunks.append(
                    Chunk(
                        chunk_index=index,
                        content=content,
                        token_count=len(window),
                        page_number=page_number,
                    )
                )
                index += 1
            start += step

    return chunks
