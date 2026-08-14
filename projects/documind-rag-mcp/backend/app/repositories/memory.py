"""In-memory repository implementations.

Used by the test suite and secret-free local runs. They enforce the same
invariants the SQL schema enforces: session isolation, the unique chunk key,
and cascade deletes — so tests exercise real behavior, not conveniences.
"""

from __future__ import annotations

import math
from typing import Optional
from uuid import UUID

from ..domain.models import (
    Chunk,
    Conversation,
    Document,
    Message,
    RetrievalLog,
    RetrievedChunk,
    utcnow,
)


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


class MemoryDocumentRepository:
    def __init__(self) -> None:
        self._docs: dict[UUID, Document] = {}

    async def create(self, document: Document) -> Document:
        self._docs[document.id] = document.model_copy(deep=True)
        return document

    async def get(self, document_id: UUID, session_id: UUID) -> Optional[Document]:
        doc = self._docs.get(document_id)
        if doc is None or doc.session_id != session_id:
            return None
        return doc.model_copy(deep=True)

    async def list_for_session(self, session_id: UUID) -> list[Document]:
        docs = [d.model_copy(deep=True) for d in self._docs.values() if d.session_id == session_id]
        return sorted(docs, key=lambda d: d.created_at)

    async def update(self, document: Document) -> Document:
        if document.id not in self._docs:
            raise KeyError(f"document {document.id} does not exist")
        document.updated_at = utcnow()
        self._docs[document.id] = document.model_copy(deep=True)
        return document

    async def delete(self, document_id: UUID, session_id: UUID) -> bool:
        doc = self._docs.get(document_id)
        if doc is None or doc.session_id != session_id:
            return False
        del self._docs[document_id]
        return True

    # Test helper for match() joins
    def unsafe_get(self, document_id: UUID) -> Optional[Document]:
        return self._docs.get(document_id)


class MemoryChunkRepository:
    def __init__(self, documents: MemoryDocumentRepository) -> None:
        self._chunks: dict[UUID, Chunk] = {}
        self._keys: set[tuple[UUID, int, int]] = set()
        self._documents = documents

    async def upsert_many(self, chunks: list[Chunk]) -> int:
        inserted = 0
        for chunk in chunks:
            key = (chunk.document_id, chunk.page_number, chunk.chunk_index)
            if key in self._keys:
                continue  # idempotent: unique (document_id, page_number, chunk_index)
            self._keys.add(key)
            self._chunks[chunk.id] = chunk.model_copy(deep=True)
            inserted += 1
        return inserted

    async def count_for_document(self, document_id: UUID) -> int:
        return sum(1 for c in self._chunks.values() if c.document_id == document_id)

    async def match(
        self,
        query_embedding: list[float],
        match_count: int,
        similarity_threshold: float,
        session_id: UUID,
        filter_document_ids: Optional[list[UUID]] = None,
    ) -> list[RetrievedChunk]:
        results: list[RetrievedChunk] = []
        for chunk in self._chunks.values():
            if chunk.embedding is None:
                continue
            doc = self._documents.unsafe_get(chunk.document_id)
            if doc is None or doc.session_id != session_id or doc.status.value != "ready":
                continue
            if filter_document_ids and chunk.document_id not in filter_document_ids:
                continue
            sim = cosine_similarity(query_embedding, chunk.embedding)
            if sim >= similarity_threshold:
                results.append(
                    RetrievedChunk(
                        chunk_id=chunk.id,
                        document_id=chunk.document_id,
                        filename=doc.filename,
                        page_number=chunk.page_number,
                        chunk_index=chunk.chunk_index,
                        content=chunk.content,
                        similarity=sim,
                    )
                )
        results.sort(key=lambda r: r.similarity, reverse=True)
        return results[:match_count]

    def delete_for_document(self, document_id: UUID) -> None:
        ids = [cid for cid, c in self._chunks.items() if c.document_id == document_id]
        for cid in ids:
            chunk = self._chunks.pop(cid)
            self._keys.discard((chunk.document_id, chunk.page_number, chunk.chunk_index))


class MemoryConversationRepository:
    def __init__(self) -> None:
        self._conversations: dict[UUID, Conversation] = {}
        self._messages: dict[UUID, list[Message]] = {}
        self._citations: dict[UUID, list[dict]] = {}

    async def create(self, conversation: Conversation) -> Conversation:
        self._conversations[conversation.id] = conversation.model_copy(deep=True)
        self._messages[conversation.id] = []
        return conversation

    async def get(self, conversation_id: UUID, session_id: UUID) -> Optional[Conversation]:
        conv = self._conversations.get(conversation_id)
        if conv is None or conv.session_id != session_id:
            return None
        return conv.model_copy(deep=True)

    async def add_message(self, message: Message) -> Message:
        if message.conversation_id not in self._messages:
            raise KeyError("conversation does not exist")
        self._messages[message.conversation_id].append(message.model_copy(deep=True))
        return message

    async def list_messages(self, conversation_id: UUID) -> list[Message]:
        return [m.model_copy(deep=True) for m in self._messages.get(conversation_id, [])]

    async def get_message_for_session(
        self, message_id: UUID, session_id: UUID
    ) -> Optional[Message]:
        for conversation_id, messages in self._messages.items():
            conversation = self._conversations.get(conversation_id)
            if conversation is None or conversation.session_id != session_id:
                continue
            for message in messages:
                if message.id == message_id:
                    return message.model_copy(deep=True)
        return None

    async def add_citations(self, message_id: UUID, citations: list[dict]) -> None:
        self._citations.setdefault(message_id, []).extend(citations)

    async def list_citations(self, message_id: UUID) -> list[dict]:
        return list(self._citations.get(message_id, []))


class MemoryRetrievalLogRepository:
    def __init__(self) -> None:
        self._logs: list[RetrievalLog] = []

    async def create(self, log: RetrievalLog) -> RetrievalLog:
        self._logs.append(log.model_copy(deep=True))
        return log

    async def get_for_message(self, message_id: UUID) -> Optional[RetrievalLog]:
        for log in self._logs:
            if log.message_id == message_id:
                return log.model_copy(deep=True)
        return None


class MemoryStorageRepository:
    def __init__(self) -> None:
        self._blobs: dict[str, bytes] = {}

    async def save(self, path: str, data: bytes, content_type: str) -> None:
        self._blobs[path] = data

    async def load(self, path: str) -> bytes:
        if path not in self._blobs:
            raise KeyError(f"no blob at {path}")
        return self._blobs[path]

    async def delete(self, path: str) -> bool:
        return self._blobs.pop(path, None) is not None
