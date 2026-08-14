"""Document service tests: upload, batched/resumable processing, delete."""

from uuid import uuid4

import pytest

from app.core.errors import NotFoundError, ValidationAppError
from app.domain.models import DocumentStatus
from tests.helpers import make_pdf

SESSION = uuid4()

PAGES = [
    "Refunds are issued within 30 days of purchase. Contact support to start a refund.",
    "Shipping takes 5 to 7 business days. Express shipping is available for a fee.",
    "Warranty coverage lasts one year from the delivery date. Damage from misuse is excluded.",
    "Returns must include the original packaging. Return shipping labels are prepaid.",
    "Gift cards are non-refundable and never expire. Balances can be checked online.",
]


class TestUpload:
    async def test_upload_persists_document_and_blob(self, world):
        doc = await world.document_service.upload(
            SESSION, "policy.pdf", "application/pdf", make_pdf(PAGES)
        )
        assert doc.status == DocumentStatus.uploaded
        assert doc.page_count == 5
        assert doc.last_processed_page == 0
        blob = await world.storage_repo.load(doc.storage_path)
        assert blob.startswith(b"%PDF-")

    async def test_upload_rejects_non_pdf(self, world):
        with pytest.raises(ValidationAppError):
            await world.document_service.upload(
                SESSION, "notes.txt", "text/plain", b"hello"
            )

    async def test_upload_rejects_spoofed_pdf(self, world):
        with pytest.raises(ValidationAppError):
            await world.document_service.upload(
                SESSION, "fake.pdf", "application/pdf", b"MZ\x90\x00 not a pdf"
            )


class TestBatchedProcessing:
    async def test_processing_advances_in_batches(self, world):
        doc = await world.document_service.upload(
            SESSION, "policy.pdf", "application/pdf", make_pdf(PAGES)
        )
        # batch size is 2 (see conftest): 5 pages -> 3 batches
        doc = await world.document_service.process_batch(doc.id, SESSION)
        assert doc.status == DocumentStatus.processing
        assert doc.last_processed_page == 2

        doc = await world.document_service.process_batch(doc.id, SESSION)
        assert doc.last_processed_page == 4
        assert doc.status == DocumentStatus.processing

        doc = await world.document_service.process_batch(doc.id, SESSION)
        assert doc.last_processed_page == 5
        assert doc.status == DocumentStatus.ready

    async def test_processing_is_idempotent_when_ready(self, world):
        doc = await world.document_service.upload(
            SESSION, "policy.pdf", "application/pdf", make_pdf(PAGES)
        )
        doc = await world.document_service.process_all(doc.id, SESSION)
        count_before = await world.chunks_repo.count_for_document(doc.id)

        doc = await world.document_service.process_batch(doc.id, SESSION)
        assert doc.status == DocumentStatus.ready
        assert await world.chunks_repo.count_for_document(doc.id) == count_before

    async def test_chunks_carry_embeddings(self, world):
        doc = await world.document_service.upload(
            SESSION, "policy.pdf", "application/pdf", make_pdf(PAGES)
        )
        await world.document_service.process_all(doc.id, SESSION)
        assert await world.chunks_repo.count_for_document(doc.id) >= 5
        for chunk in world.chunks_repo._chunks.values():
            assert chunk.embedding is not None

    async def test_embedding_failure_does_not_advance_progress(self, world):
        doc = await world.document_service.upload(
            SESSION, "policy.pdf", "application/pdf", make_pdf(PAGES)
        )

        class ExplodingEmbeddings:
            async def embed_texts(self, texts):
                raise RuntimeError("provider down")

            async def embed_query(self, text):
                raise RuntimeError("provider down")

        good = world.document_service._embeddings
        world.document_service._embeddings = ExplodingEmbeddings()
        with pytest.raises(Exception):
            await world.document_service.process_batch(doc.id, SESSION)

        refreshed = await world.document_service.get(doc.id, SESSION)
        assert refreshed.last_processed_page == 0  # no progress on failure
        assert refreshed.status == DocumentStatus.processing

        # Recovery: restore the provider and the same batch succeeds cleanly.
        world.document_service._embeddings = good
        doc = await world.document_service.process_all(doc.id, SESSION)
        assert doc.status == DocumentStatus.ready

    async def test_process_missing_document_404s(self, world):
        with pytest.raises(NotFoundError):
            await world.document_service.process_batch(uuid4(), SESSION)

    async def test_process_other_sessions_document_404s(self, world):
        doc = await world.document_service.upload(
            SESSION, "policy.pdf", "application/pdf", make_pdf(PAGES)
        )
        with pytest.raises(NotFoundError):
            await world.document_service.process_batch(doc.id, uuid4())


class TestDelete:
    async def test_delete_removes_document_and_blob(self, world):
        doc = await world.document_service.upload(
            SESSION, "policy.pdf", "application/pdf", make_pdf(PAGES)
        )
        await world.document_service.process_all(doc.id, SESSION)
        await world.document_service.delete(doc.id, SESSION)

        with pytest.raises(NotFoundError):
            await world.document_service.get(doc.id, SESSION)
        with pytest.raises(KeyError):
            await world.storage_repo.load(doc.storage_path)

    async def test_delete_other_sessions_document_404s(self, world):
        doc = await world.document_service.upload(
            SESSION, "policy.pdf", "application/pdf", make_pdf(PAGES)
        )
        with pytest.raises(NotFoundError):
            await world.document_service.delete(doc.id, uuid4())
