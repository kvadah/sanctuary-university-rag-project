import uuid
from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, ConfigDict
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
