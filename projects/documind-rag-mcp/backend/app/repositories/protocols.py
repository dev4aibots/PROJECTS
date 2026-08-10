"""Repository protocols — the persistence boundary.

Services depend only on these protocols. Implementations:
  - memory.py    : in-memory (tests, secret-free local dev)
  - supabase.py  : Supabase PostgREST + Storage (live)
"""

from __future__ import annotations

from typing import Optional, Protocol
from uuid import UUID

from ..domain.models import (
    Chunk,
    Conversation,
    Document,
    Message,
    RetrievalLog,
    RetrievedChunk,
)


class DocumentRepository(Protocol):
    async def create(self, document: Document) -> Document: ...

    async def get(self, document_id: UUID, session_id: UUID) -> Optional[Document]: ...

    async def list_for_session(self, session_id: UUID) -> list[Document]: ...

    async def update(self, document: Document) -> Document: ...

    async def delete(self, document_id: UUID, session_id: UUID) -> bool: ...


class ChunkRepository(Protocol):
    async def upsert_many(self, chunks: list[Chunk]) -> int:
        """Insert chunks idempotently by (document_id, page_number, chunk_index).

        Returns the number of chunks newly inserted (duplicates are ignored).
        """
        ...

    async def count_for_document(self, document_id: UUID) -> int: ...

    async def match(
        self,
        query_embedding: list[float],
        match_count: int,
        similarity_threshold: float,
        session_id: UUID,
        filter_document_ids: Optional[list[UUID]] = None,
    ) -> list[RetrievedChunk]: ...


class ConversationRepository(Protocol):
    async def create(self, conversation: Conversation) -> Conversation: ...

    async def get(self, conversation_id: UUID, session_id: UUID) -> Optional[Conversation]: ...

    async def add_message(self, message: Message) -> Message: ...

    async def list_messages(self, conversation_id: UUID) -> list[Message]: ...

    async def get_message_for_session(
        self, message_id: UUID, session_id: UUID
    ) -> Optional[Message]: ...

    async def add_citations(self, message_id: UUID, citations: list[dict]) -> None: ...

    async def list_citations(self, message_id: UUID) -> list[dict]: ...


class RetrievalLogRepository(Protocol):
    async def create(self, log: RetrievalLog) -> RetrievalLog: ...

    async def get_for_message(self, message_id: UUID) -> Optional[RetrievalLog]: ...


class StorageRepository(Protocol):
    async def save(self, path: str, data: bytes, content_type: str) -> None: ...

    async def load(self, path: str) -> bytes: ...

    async def delete(self, path: str) -> bool: ...
