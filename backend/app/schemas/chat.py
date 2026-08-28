import uuid
from datetime import datetime
from typing import Optional, List, Any, Dict, Literal
from pydantic import BaseModel, ConfigDict, Field
from app.models.chat import MessageRole
from app.schemas.common import PaginationMeta


class ChatQueryRequest(BaseModel):
    conversation_id: Optional[uuid.UUID] = None
    query: str
    academic_term: Optional[str] = None


class Citation(BaseModel):
    index: int
    document_id: uuid.UUID
    document_title: str
    chunk_id: uuid.UUID
    page_number: Optional[int] = None
    section_title: Optional[str] = None
    score: float
    snippet: str


class ChatQueryResponse(BaseModel):
    conversation_id: uuid.UUID
    message_id: uuid.UUID
    answer: str
    citations: List[Citation] = []
    meta: Dict[str, Any] = {}


class PublicChatTurn(BaseModel):
    """One prior turn supplied by an anonymous client (no server-side history)."""
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=8000)


class PublicChatQueryRequest(BaseModel):
    """A guest question. Since nothing is persisted, the client sends its own
    recent turns in ``history`` (capped server-side)."""
    query: str = Field(min_length=1, max_length=4000)
    academic_term: Optional[str] = None
    history: Optional[List[PublicChatTurn]] = None


class PublicChatQueryResponse(BaseModel):
    """Guest answer — no conversation_id / message_id because nothing is stored."""
    answer: str
    citations: List[Citation] = []
    meta: Dict[str, Any] = {}


class MessageRead(BaseModel):
    id: uuid.UUID
    conversation_id: uuid.UUID
    role: MessageRole
    content: str
    citations: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConversationCreate(BaseModel):
    title: Optional[str] = "New Conversation"


class ConversationSummary(BaseModel):
    id: uuid.UUID
    title: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConversationRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    messages: List[MessageRead] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConversationListResponse(BaseModel):
    items: List[ConversationSummary]
    pagination: PaginationMeta


class FeedbackCreate(BaseModel):
    message_id: uuid.UUID
    rating: int # 1 or -1
    comment: Optional[str] = None


class FeedbackRead(BaseModel):
    id: uuid.UUID
    message_id: uuid.UUID
    user_id: uuid.UUID
    rating: int
    comment: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
