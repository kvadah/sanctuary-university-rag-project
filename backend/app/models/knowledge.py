import enum
import uuid
from typing import Optional, List
from sqlalchemy import String, Text, Boolean, Integer, Enum as SQLEnum, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel


class DocumentClassification(str, enum.Enum):
    PUBLIC = "PUBLIC"
    STUDENT = "STUDENT"
    FACULTY = "FACULTY"
    STAFF = "STAFF"
    ADMIN = "ADMIN"


class KnowledgeSourceType(str, enum.Enum):
    PDF = "PDF"
    DOCX = "DOCX"
    EXCEL = "EXCEL"
    POWERPOINT = "POWERPOINT"
    WEB = "WEB"
    FAQ = "FAQ"
    DATABASE = "DATABASE"
    API = "API"


class SyncStatus(str, enum.Enum):
    IDLE = "IDLE"
    SYNCING = "SYNCING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class KnowledgeSource(BaseModel):
    __tablename__ = "knowledge_sources"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_type: Mapped[KnowledgeSourceType] = mapped_column(
        SQLEnum(KnowledgeSourceType, name="knowledge_source_type_enum"),
        nullable=False,
    )
    config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_synced_at: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    sync_status: Mapped[SyncStatus] = mapped_column(
        SQLEnum(SyncStatus, name="sync_status_enum"),
        default=SyncStatus.IDLE,
        nullable=False,
    )

    documents: Mapped[List["Document"]] = relationship("Document", back_populates="source", cascade="all, delete-orphan")


class Document(BaseModel):
    __tablename__ = "documents"

    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)
    classification: Mapped[DocumentClassification] = mapped_column(
        SQLEnum(DocumentClassification, name="document_classification_enum"),
        default=DocumentClassification.PUBLIC,
        nullable=False,
        index=True,
    )
    academic_term: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True) # e.g. "Fall 2026"
    is_current: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    meta_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    source: Mapped["KnowledgeSource"] = relationship("KnowledgeSource", back_populates="documents")
    versions: Mapped[List["DocumentVersion"]] = relationship("DocumentVersion", back_populates="document", cascade="all, delete-orphan")
    chunks: Mapped[List["DocumentChunk"]] = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")


class DocumentVersion(BaseModel):
    __tablename__ = "document_versions"

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    academic_term: Mapped[str] = mapped_column(String(50), nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    change_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    document: Mapped["Document"] = relationship("Document", back_populates="versions")


class DocumentChunk(BaseModel):
    __tablename__ = "document_chunks"

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, nullable=False)
    page_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    section_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    vector_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True) # Point ID in Qdrant
    meta_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    document: Mapped["Document"] = relationship("Document", back_populates="chunks")
