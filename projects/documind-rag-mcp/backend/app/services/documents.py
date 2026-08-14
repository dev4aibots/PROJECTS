"""Document service: upload, batched processing with resume, list, delete.

Processing is batched (N pages per call) and resumable: `last_processed_page`
tracks progress, chunk upserts are idempotent by (document_id, page_number,
chunk_index), so a crashed or repeated batch never duplicates data.
"""

from __future__ import annotations

from uuid import UUID, uuid4

from ..core.errors import NotFoundError, StorageError, ValidationAppError
from ..domain.chunking import chunk_pages
from ..domain.models import Document, DocumentStatus
from ..domain.pdf import extract_pages, validate_pdf_upload
from ..providers.protocols import EmbeddingProvider
from ..repositories.protocols import (
    ChunkRepository,
    DocumentRepository,
    StorageRepository,
)


class DocumentService:
    def __init__(
        self,
        documents: DocumentRepository,
        chunks: ChunkRepository,
        storage: StorageRepository,
        embeddings: EmbeddingProvider,
        max_upload_bytes: int = 10 * 1024 * 1024,
        pages_per_batch: int = 3,
        chunk_target_tokens: int = 800,
        chunk_overlap_ratio: float = 0.15,
    ) -> None:
        self._documents = documents
        self._chunks = chunks
        self._storage = storage
        self._embeddings = embeddings
        self._max_upload_bytes = max_upload_bytes
        self._pages_per_batch = pages_per_batch
        self._chunk_target_tokens = chunk_target_tokens
        self._chunk_overlap_ratio = chunk_overlap_ratio

    async def upload(
        self, session_id: UUID, filename: str, content_type: str, data: bytes
    ) -> Document:
        """Validate and persist an uploaded PDF; processing happens separately."""
        page_count = validate_pdf_upload(
            filename, content_type, data, self._max_upload_bytes
        )
        storage_path = f"{session_id}/{uuid4()}.pdf"
        try:
            await self._storage.save(storage_path, data, "application/pdf")
        except Exception:
            raise StorageError() from None

        document = Document(
            filename=filename,
            content_type="application/pdf",
            file_size=len(data),
            storage_path=storage_path,
            status=DocumentStatus.uploaded,
            page_count=page_count,
            session_id=session_id,
        )
        return await self._documents.create(document)

    async def process_batch(self, document_id: UUID, session_id: UUID) -> Document:
        """Process the next batch of pages. Safe to call repeatedly.

        Returns the updated document; status becomes `ready` once
        last_processed_page reaches page_count.
        """
        document = await self._documents.get(document_id, session_id)
        if document is None:
            raise NotFoundError("Document not found.")
        if document.status == DocumentStatus.ready:
            return document  # idempotent no-op
        if document.status == DocumentStatus.failed:
            raise ValidationAppError(
                "This document failed processing; delete and re-upload it."
            )

        assert document.page_count is not None
        first = document.last_processed_page + 1
        last = min(document.page_count, first + self._pages_per_batch - 1)

        try:
            data = await self._storage.load(document.storage_path)
        except Exception:
            document.status = DocumentStatus.failed
            document.processing_error = "stored file is unreadable"
            await self._documents.update(document)
            raise StorageError("The stored document could not be read.") from None

        try:
            pages = extract_pages(data, first, last)
            chunks = chunk_pages(
                document.id,
                pages,
                target_tokens=self._chunk_target_tokens,
                overlap_ratio=self._chunk_overlap_ratio,
            )
            if chunks:
                vectors = await self._embeddings.embed_texts(
                    [c.content for c in chunks]
                )
                for chunk, vector in zip(chunks, vectors):
                    chunk.embedding = vector
                await self._chunks.upsert_many(chunks)
        except Exception as e:
            # Progress is NOT advanced: the batch can be retried after the
            # transient cause (e.g. embedding provider outage) clears.
            document.status = DocumentStatus.processing
            document.processing_error = "batch failed; retry processing"
            await self._documents.update(document)
            if isinstance(e, StorageError):
                raise
            from ..core.errors import AppError

            if isinstance(e, AppError):
                raise
            raise StorageError("Document processing failed for this batch.") from None

        document.last_processed_page = last
        document.processing_error = None
        if last >= document.page_count:
            document.status = DocumentStatus.ready
        else:
            document.status = DocumentStatus.processing
        return await self._documents.update(document)

    async def process_all(self, document_id: UUID, session_id: UUID) -> Document:
        """Drive process_batch to completion (used by tests and the API)."""
        document = await self.process_batch(document_id, session_id)
        while document.status == DocumentStatus.processing:
            document = await self.process_batch(document_id, session_id)
        return document

    async def get(self, document_id: UUID, session_id: UUID) -> Document:
        document = await self._documents.get(document_id, session_id)
        if document is None:
            raise NotFoundError("Document not found.")
        return document

    async def list(self, session_id: UUID) -> list[Document]:
        return await self._documents.list_for_session(session_id)

    async def delete(self, document_id: UUID, session_id: UUID) -> None:
        document = await self._documents.get(document_id, session_id)
        if document is None:
            raise NotFoundError("Document not found.")
        try:
            await self._storage.delete(document.storage_path)
        except Exception:
            pass  # blob cleanup is best-effort; the DB row is the source of truth
        await self._documents.delete(document_id, session_id)
