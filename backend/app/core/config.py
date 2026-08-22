import os
from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "KnowledgeHub AI — Sanctuary University"
    VERSION: str = "1.1"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
    ]

    # Security & Authentication
    SECRET_KEY: str = "super-secret-key-change-in-production-knowledgehub-ai"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: str = "5432"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres_password"
    POSTGRES_DB: str = "knowledgehub"

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def SYNC_SQLALCHEMY_DATABASE_URI(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # Qdrant Vector Database
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_GRPC_PORT: int = 6334
    QDRANT_API_KEY: str = ""

    # Redis Cache & Task Broker
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""

    @property
    def REDIS_URL(self) -> str:
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/0"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    # MinIO / S3 Storage
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET_DOCUMENTS: str = "knowledgehub-documents"
    MINIO_SECURE: bool = False

    # AI Model Providers
    # The app talks to LLMs through the OpenAI SDK. LLM_PROVIDER selects which
    # backend that SDK points at: "gemini" (Google AI Studio, free tier — the
    # default) via its OpenAI-compatible endpoint, or "openai" for OpenAI proper.
    LLM_PROVIDER: str = "gemini"
    OPENAI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    # Gemini's OpenAI-compatible surface: https://ai.google.dev/gemini-api/docs/openai
    GEMINI_BASE_URL: str = "https://generativelanguage.googleapis.com/v1beta/openai/"
    DEFAULT_EMBEDDING_MODEL: str = "gemini-embedding-001"  # Gemini, 3072-dim (default)
    DEFAULT_LLM_MODEL: str = "gemini-3.6-flash"  # gemini-2.5-flash was retired for new users (404)

    @property
    def LLM_API_KEY(self) -> str:
        """API key for the active provider (see LLM_PROVIDER)."""
        if self.LLM_PROVIDER == "openai":
            return self.OPENAI_API_KEY
        return self.GEMINI_API_KEY

    @property
    def LLM_BASE_URL(self) -> str:
        """Base URL for the active provider — empty means the SDK's OpenAI default."""
        if self.LLM_PROVIDER == "openai":
            return ""
        return self.GEMINI_BASE_URL

    # RAG pipeline
    EMBEDDING_DIM: int = 3072  # must match DEFAULT_EMBEDDING_MODEL's output size
    QDRANT_COLLECTION: str = "document_chunks"
    CHUNK_MAX_TOKENS: int = 500
    CHUNK_OVERLAP_TOKENS: int = 75
    RAG_TOP_K: int = 5  # final chunks handed to the generator
    # Hybrid retrieval + memory (see app/retrieval/)
    RAG_CANDIDATE_K: int = 20  # candidates each retriever returns before fusion/rerank
    RAG_RRF_K: int = 60  # Reciprocal Rank Fusion damping constant
    RAG_HISTORY_TURNS: int = 6  # recent messages fed to retrieval + generation
    RAG_RERANK_ENABLED: bool = True  # LLM rerank of fused candidates
    RAG_QUERY_REWRITE_ENABLED: bool = True  # LLM rewrite of follow-ups before retrieval

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
