"""Supabase repository implementations over PostgREST + Storage HTTP APIs.

Uses plain httpx (serverless-friendly, no long-lived connections). These
implementations are exercised live only when SUPABASE_URL and the service
role key are configured; the offline test suite uses the memory
implementations against the same protocols.
"""

from __future__ import annotations

import json
from typing import Any, Optional
from uuid import UUID

import httpx

from ..core.errors import StorageError
from ..core.settings import Settings
from ..domain.models import (
    Chunk,
    Conversation,
    Document,
    DocumentStatus,
    Message,
    RetrievalLog,
    RetrievedChunk,
)

_TIMEOUT = httpx.Timeout(20.0)


class SupabaseClient:
    """Thin async wrapper over PostgREST and Storage endpoints."""

    def __init__(self, settings: Settings) -> None:
        if not settings.supabase_url or not settings.supabase_service_role_key:
            raise ValueError("Supabase credentials are not configured")
        self.base = settings.supabase_url.rstrip("/")
        self.bucket = settings.supabase_storage_bucket
        self._headers = {
            "apikey": settings.supabase_service_role_key,
            "Authorization": f"Bearer {settings.supabase_service_role_key}",
        }

    def _rest(self, table: str) -> str:
        return f"{self.base}/rest/v1/{table}"

    async def select(self, table: str, params: dict[str, str]) -> list[dict]:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(self._rest(table), params=params, headers=self._headers)
            resp.raise_for_status()
            return resp.json()

    async def insert(self, table: str, rows: list[dict], *, upsert_ignore: bool = False) -> list[dict]:
        headers = dict(self._headers)
        headers["Content-Type"] = "application/json"
        headers["Prefer"] = "return=representation"
        if upsert_ignore:
            headers["Prefer"] = "resolution=ignore-duplicates,return=representation"
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(self._rest(table), content=json.dumps(rows), headers=headers)
            resp.raise_for_status()
            return resp.json() if resp.content else []

    async def update(self, table: str, params: dict[str, str], patch: dict) -> list[dict]:
        headers = dict(self._headers)
        headers["Content-Type"] = "application/json"
        headers["Prefer"] = "return=representation"
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.patch(
                self._rest(table), params=params, content=json.dumps(patch), headers=headers
            )
            resp.raise_for_status()
            return resp.json() if resp.content else []

    async def delete(self, table: str, params: dict[str, str]) -> int:
        headers = dict(self._headers)
        headers["Prefer"] = "return=representation"
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.delete(self._rest(table), params=params, headers=headers)
            resp.raise_for_status()
            body = resp.json() if resp.content else []
            return len(body)

    async def rpc(self, function: str, payload: dict[str, Any]) -> Any:
        headers = dict(self._headers)
        headers["Content-Type"] = "application/json"
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(
                f"{self.base}/rest/v1/rpc/{function}", content=json.dumps(payload), headers=headers
            )
            resp.raise_for_status()
            return resp.json()

    # Storage
    async def storage_upload(self, path: str, data: bytes, content_type: str) -> None:
        headers = dict(self._headers)
        headers["Content-Type"] = content_type
        headers["x-upsert"] = "true"
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(
                f"{self.base}/storage/v1/object/{self.bucket}/{path}", content=data, headers=headers
            )
            if resp.status_code >= 400:
                raise StorageError()

    async def storage_download(self, path: str) -> bytes:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(
                f"{self.base}/storage/v1/object/{self.bucket}/{path}", headers=self._headers
            )
            if resp.status_code >= 400:
                raise StorageError("Document file could not be read from storage.")
            return resp.content

    async def storage_delete(self, path: str) -> bool:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.delete(
                f"{self.base}/storage/v1/object/{self.bucket}/{path}", headers=self._headers
            )
            return resp.status_code < 400


def _doc_from_row(row: dict) -> Document:
    return Document(
        id=UUID(row["id"]),
        filename=row["filename"],
        content_type=row["content_type"],
        file_size=row["file_size"],
        storage_path=row["storage_path"],
        status=DocumentStatus(row["status"]),
        page_count=row.get("page_count"),
        last_processed_page=row.get("last_processed_page", 0),
        processing_error=row.get("processing_error"),
        session_id=UUID(row["session_id"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


class SupabaseDocumentRepository:
    def __init__(self, client: SupabaseClient) -> None:
        self.client = client

    async def create(self, document: Document) -> Document:
        row = json.loads(document.model_dump_json())
        await self.client.insert("documents", [row])
        return document

    async def get(self, document_id: UUID, session_id: UUID) -> Optional[Document]:
        rows = await self.client.select(
            "documents",
            {"id": f"eq.{document_id}", "session_id": f"eq.{session_id}", "select": "*"},
        )
        return _doc_from_row(rows[0]) if rows else None

    async def list_for_session(self, session_id: UUID) -> list[Document]:
        rows = await self.client.select(
            "documents",
            {"session_id": f"eq.{session_id}", "select": "*", "order": "created_at.asc"},
        )
        return [_doc_from_row(r) for r in rows]

    async def update(self, document: Document) -> Document:
        patch = json.loads(document.model_dump_json(exclude={"id", "created_at"}))
        await self.client.update("documents", {"id": f"eq.{document.id}"}, patch)
        return document

    async def delete(self, document_id: UUID, session_id: UUID) -> bool:
        count = await self.client.delete(
            "documents", {"id": f"eq.{document_id}", "session_id": f"eq.{session_id}"}
        )
        return count > 0


class SupabaseChunkRepository:
    def __init__(self, client: SupabaseClient) -> None:
        self.client = client

    async def upsert_many(self, chunks: list[Chunk]) -> int:
        if not chunks:
            return 0
        rows = [json.loads(c.model_dump_json()) for c in chunks]
        inserted = await self.client.insert("document_chunks", rows, upsert_ignore=True)
        return len(inserted)

    async def count_for_document(self, document_id: UUID) -> int:
        rows = await self.client.select(
            "document_chunks", {"document_id": f"eq.{document_id}", "select": "id"}
        )
        return len(rows)

    async def match(
        self,
        query_embedding: list[float],
        match_count: int,
        similarity_threshold: float,
        session_id: UUID,
        filter_document_ids: Optional[list[UUID]] = None,
    ) -> list[RetrievedChunk]:
        payload: dict[str, Any] = {
            "query_embedding": query_embedding,
            "match_count": match_count,
            "similarity_threshold": similarity_threshold,
            "filter_session_id": str(session_id),
            "filter_document_ids": [str(d) for d in filter_document_ids]
            if filter_document_ids
            else None,
        }
        rows = await self.client.rpc("match_document_chunks", payload)
        results = []
        for row in rows:
            results.append(
                RetrievedChunk(
                    chunk_id=UUID(row["chunk_id"]),
                    document_id=UUID(row["document_id"]),
                    page_number=row["page_number"],
                    chunk_index=row["chunk_index"],
                    content=row["content"],
                    similarity=row["similarity"],
                )
            )
        return results


class SupabaseConversationRepository:
    def __init__(self, client: SupabaseClient) -> None:
        self.client = client

    async def create(self, conversation: Conversation) -> Conversation:
        await self.client.insert("conversations", [json.loads(conversation.model_dump_json())])
        return conversation

    async def get(self, conversation_id: UUID, session_id: UUID) -> Optional[Conversation]:
        rows = await self.client.select(
            "conversations",
            {"id": f"eq.{conversation_id}", "session_id": f"eq.{session_id}", "select": "*"},
        )
        if not rows:
            return None
        row = rows[0]
        return Conversation(
            id=UUID(row["id"]),
            session_id=UUID(row["session_id"]),
            title=row.get("title"),
            created_at=row["created_at"],
        )

    async def add_message(self, message: Message) -> Message:
        await self.client.insert("messages", [json.loads(message.model_dump_json())])
        return message

    @staticmethod
    def _message_from_row(row: dict) -> Message:
        return Message(
            id=UUID(row["id"]),
            conversation_id=UUID(row["conversation_id"]),
            role=row["role"],
            content=row["content"],
            grounded=row.get("grounded"),
            confidence=row.get("confidence"),
            created_at=row["created_at"],
        )

    async def list_messages(self, conversation_id: UUID) -> list[Message]:
        rows = await self.client.select(
            "messages",
            {"conversation_id": f"eq.{conversation_id}", "select": "*", "order": "created_at.asc"},
        )
        return [self._message_from_row(row) for row in rows]

    async def get_message_for_session(
        self, message_id: UUID, session_id: UUID
    ) -> Optional[Message]:
        rows = await self.client.select(
            "messages",
            {"id": f"eq.{message_id}", "select": "*"},
        )
        if not rows:
            return None
        message = self._message_from_row(rows[0])
        conversation = await self.get(message.conversation_id, session_id)
        return message if conversation is not None else None

    async def add_citations(self, message_id: UUID, citations: list[dict]) -> None:
        if not citations:
            return
        # Citation dict shape is defined by ChatService.ask:
        # {document_id, filename, page, excerpt, chunk_id}
        rows = [
            {
                "message_id": str(message_id),
                "chunk_id": str(c["chunk_id"]) if c.get("chunk_id") else None,
                "document_id": str(c["document_id"]),
                "filename": c.get("filename", ""),
                "page_number": c["page"],
                "excerpt": c["excerpt"],
            }
            for c in citations
        ]
        await self.client.insert("message_citations", rows)

    async def list_citations(self, message_id: UUID) -> list[dict]:
        return await self.client.select(
            "message_citations", {"message_id": f"eq.{message_id}", "select": "*"}
        )


class SupabaseRetrievalLogRepository:
    def __init__(self, client: SupabaseClient) -> None:
        self.client = client

    async def create(self, log: RetrievalLog) -> RetrievalLog:
        await self.client.insert("retrieval_logs", [json.loads(log.model_dump_json())])
        return log

    async def get_for_message(self, message_id: UUID) -> Optional[RetrievalLog]:
        rows = await self.client.select(
            "retrieval_logs", {"message_id": f"eq.{message_id}", "select": "*"}
        )
        if not rows:
            return None
        r = rows[0]
        return RetrievalLog(
            id=UUID(r["id"]),
            message_id=UUID(r["message_id"]) if r.get("message_id") else None,
            query=r["query"],
            top_k=r["top_k"],
            threshold=r["threshold"],
            returned_count=r["returned_count"],
            max_similarity=r.get("max_similarity"),
            duration_ms=r["duration_ms"],
            created_at=r["created_at"],
        )


class SupabaseStorageRepository:
    def __init__(self, client: SupabaseClient) -> None:
        self.client = client

    async def save(self, path: str, data: bytes, content_type: str) -> None:
        await self.client.storage_upload(path, data, content_type)

    async def load(self, path: str) -> bytes:
        return await self.client.storage_download(path)

    async def delete(self, path: str) -> bool:
        return await self.client.storage_delete(path)
