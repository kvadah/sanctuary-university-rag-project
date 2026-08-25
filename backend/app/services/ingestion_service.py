"""Ingestion pipeline: parse -> chunk -> embed -> Qdrant + Postgres.

The request no longer runs this inline; it archives the upload and enqueues a
Celery job (see ``ingestion_job_service`` + ``app.workers.tasks``). The worker
calls :meth:`IngestionService.ingest_bytes` on its persistent event loop. Parsing
is CPU-bound and runs in a threadpool so it never blocks whichever loop drives it.
"""
import uuid
from typing import Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.connectors.parsers import extract_pages
from app.core.config import settings
from app.llm.embeddings import EmbeddingClient
from app.models.knowledge import (
    Document,
    DocumentChunk,
    DocumentClassification,
    KnowledgeSourceType,
)
from app.repositories.document_repository import (
    DocumentChunkRepository,
    DocumentRepository,
)
from app.repositories.knowledge_repository import KnowledgeSourceRepository
from app.retrieval.vector_store import QdrantVectorStore
from app.utils.chunking import chunk_pages

# Uploaded extension -> the KnowledgeSource type used to group it.
_EXT_TO_SOURCE_TYPE = {
    "pdf": KnowledgeSourceType.PDF,
    "docx": KnowledgeSourceType.DOCX,
    "txt": KnowledgeSourceType.FAQ,
}


def resolve_file_type(filename: Optional[str]) -> str:
    """Map a filename to a supported ingest type, or raise ``HTTPException`` 400.

    Module-level so the request side can validate (and reject) an upload before a
    job is ever created, and the worker can re-resolve from the stored filename.
    """
    if not filename or "." not in filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot determine file type from filename.",
        )
    ext = filename.rsplit(".", 1)[1].lower()
    if ext not in _EXT_TO_SOURCE_TYPE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '.{ext}'. Supported: pdf, docx, txt.",
        )
    return ext


def source_type_for(file_type: str) -> KnowledgeSourceType:
    """The KnowledgeSource type that groups uploads of ``file_type``."""
    return _EXT_TO_SOURCE_TYPE[file_type]


class IngestionService:
    def __init__(self, db: AsyncSession):
        self.sources = KnowledgeSourceRepository(db)
        self.documents = DocumentRepository(db)
        self.chunks = DocumentChunkRepository(db)
        self.embeddings = EmbeddingClient()
        self.store = QdrantVectorStore()

    async def ingest_bytes(
        self,
        *,
        data: bytes,
        file_type: str,
        source_id: uuid.UUID,
        title: Optional[str],
        filename: Optional[str],
        classification: DocumentClassification,
        academic_term: Optional[str],
        file_path: Optional[str] = None,
    ) -> Tuple[Document, int]:
        """Run the full pipeline on already-read bytes and a resolved source.

        Returns the persisted :class:`Document` and its chunk count. ``file_path``
        is the MinIO object key of the archived original, stored on the document.
        """
        if not data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty.",
            )

        try:
            pages = await run_in_threadpool(extract_pages, data, file_type)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
            )

        parsed_chunks = chunk_pages(
            pages, settings.CHUNK_MAX_TOKENS, settings.CHUNK_OVERLAP_TOKENS
        )
        if not parsed_chunks:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No extractable text found in the document.",
            )

        document = await self.documents.create(
            source_id=source_id,
            title=title or filename,
            file_type=file_type,
            classification=classification,
            academic_term=academic_term,
            file_path=file_path,
        )

        vectors = await self.embeddings.embed_texts(
            [c.content for c in parsed_chunks]
        )

        chunk_rows = []
        points = []
        for parsed, vector in zip(parsed_chunks, vectors):
            chunk_id = uuid.uuid4()
            chunk_rows.append(
                DocumentChunk(
                    id=chunk_id,
                    document_id=document.id,
                    chunk_index=parsed.chunk_index,
                    content=parsed.content,
                    token_count=parsed.token_count,
                    page_number=parsed.page_number,
                    section_title=parsed.section_title,
                    vector_id=str(chunk_id),
                )
            )
            points.append(
                {
                    "id": str(chunk_id),
                    "vector": vector,
                    "payload": {
                        "chunk_id": str(chunk_id),
                        "document_id": str(document.id),
                        "document_title": document.title,
                        "classification": classification.value,
                        "academic_term": academic_term,
                        "is_current": True,
                        "page_number": parsed.page_number,
                        "section_title": parsed.section_title,
                        "content": parsed.content,
                    },
                }
            )

        await self.chunks.bulk_create(chunk_rows)
        await self.store.ensure_collection()
        await self.store.upsert(points)
        return document, len(chunk_rows)
