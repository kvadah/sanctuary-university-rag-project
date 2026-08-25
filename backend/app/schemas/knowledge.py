import uuid
from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, ConfigDict
from app.models.audit import IndexingStatus
from app.models.knowledge import KnowledgeSourceType, DocumentClassification, SyncStatus
from app.schemas.common import PaginationMeta


class KnowledgeSourceCreate(BaseModel):
    name: str
    description: Optional[str] = None
    source_type: KnowledgeSourceType
    config: Optional[Dict[str, Any]] = None


class KnowledgeSourceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class KnowledgeSourceRead(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str] = None
    source_type: KnowledgeSourceType
    config: Optional[Dict[str, Any]] = None
    is_active: bool
    last_synced_at: Optional[str] = None
    sync_status: SyncStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class KnowledgeSourceListResponse(BaseModel):
    items: List[KnowledgeSourceRead]
    pagination: PaginationMeta


class DocumentRead(BaseModel):
    id: uuid.UUID
    source_id: uuid.UUID
    title: str
    file_path: Optional[str] = None
    url: Optional[str] = None
    file_type: str
    classification: DocumentClassification
    academic_term: Optional[str] = None
    is_current: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentChunkRead(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    chunk_index: int
    content: str
    token_count: int
    page_number: Optional[int] = None
    section_title: Optional[str] = None
    vector_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class DocumentIngestResponse(BaseModel):
    document: DocumentRead
    chunk_count: int


class DocumentListResponse(BaseModel):
    items: List[DocumentRead]
    pagination: PaginationMeta


class IndexingJobRead(BaseModel):
    id: uuid.UUID
    source_id: uuid.UUID
    status: IndexingStatus
    total_documents: int
    processed_documents: int
    chunk_count: int
    error_message: Optional[str] = None
    original_filename: Optional[str] = None
    document_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class IndexingJobListResponse(BaseModel):
    items: List[IndexingJobRead]
