"""Domain models: internal entities and API/LLM structured outputs.

Pydantic v2 everywhere. These models are the single contract shared by the
REST API, the MCP facade, and the frontend types.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class DocumentStatus(str, Enum):
    uploaded = "uploaded"
    processing = "processing"
    ready = "ready"
    failed = "failed"


class Document(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    filename: str
    content_type: str
    file_size: int = Field(gt=0, le=10 * 1024 * 1024)
    storage_path: str
    status: DocumentStatus = DocumentStatus.uploaded
    page_count: Optional[int] = None
    last_processed_page: int = 0
    processing_error: Optional[str] = None
    session_id: UUID
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class Chunk(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    document_id: UUID
    page_number: int = Field(ge=1)
    chunk_index: int = Field(ge=0)
    content: str
    token_count: int = Field(ge=0)
    embedding: Optional[list[float]] = None
    created_at: datetime = Field(default_factory=utcnow)


class RetrievedChunk(BaseModel):
    chunk_id: UUID
    document_id: UUID
    filename: str = ""
    page_number: int
    chunk_index: int
    content: str
    similarity: float


class Conversation(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    session_id: UUID
    title: Optional[str] = None
    created_at: datetime = Field(default_factory=utcnow)


class Message(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    conversation_id: UUID
    role: str
    content: str
    grounded: Optional[bool] = None
    confidence: Optional[float] = None
    created_at: datetime = Field(default_factory=utcnow)

    @field_validator("role")
    @classmethod
    def _role_valid(cls, v: str) -> str:
        if v not in ("user", "assistant"):
            raise ValueError("role must be 'user' or 'assistant'")
        return v


class Citation(BaseModel):
    document_id: UUID
    filename: str
    page: int
    excerpt: str
    chunk_id: Optional[UUID] = None


class GroundedAnswer(BaseModel):
    """The structured answer contract; confidence is derived, never invented."""

    answer: str
    citations: list[Citation] = Field(default_factory=list)
    grounded: bool
    confidence: float = Field(ge=0.0, le=1.0)


class LLMAnswerDraft(BaseModel):
    """What we require the LLM to emit (before deterministic validation)."""

    answer: str
    citations: list[dict] = Field(default_factory=list)


class RetrievalLog(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    message_id: Optional[UUID] = None
    query: str
    top_k: int
    threshold: float
    returned_count: int
    max_similarity: Optional[float] = None
    duration_ms: int
    created_at: datetime = Field(default_factory=utcnow)


REFUSAL_TEXT = (
    "I couldn't find sufficient evidence in the indexed documents to answer "
    "this question."
)


def make_refusal() -> GroundedAnswer:
    return GroundedAnswer(answer=REFUSAL_TEXT, citations=[], grounded=False, confidence=0.0)
