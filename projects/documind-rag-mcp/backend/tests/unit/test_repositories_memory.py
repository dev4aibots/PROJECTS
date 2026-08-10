"""Phase 1 persistence-boundary tests: isolation, idempotency, cascade."""

import pytest
from uuid import uuid4

from app.domain.models import Chunk, Conversation, Document, DocumentStatus, Message
from app.repositories.memory import (
    MemoryChunkRepository,
    MemoryConversationRepository,
    MemoryDocumentRepository,
    MemoryRetrievalLogRepository,
    MemoryStorageRepository,
)


def make_doc(session_id=None, status=DocumentStatus.ready) -> Document:
    return Document(
        filename="policy.pdf",
        content_type="application/pdf",
        file_size=1234,
        storage_path=f"docs/{uuid4()}.pdf",
        status=status,
        session_id=session_id or uuid4(),
    )


@pytest.mark.asyncio
async def test_document_session_isolation():
    repo = MemoryDocumentRepository()
    owner = uuid4()
    intruder = uuid4()
    doc = make_doc(session_id=owner)
    await repo.create(doc)

    assert await repo.get(doc.id, owner) is not None
    assert await repo.get(doc.id, intruder) is None
    assert await repo.list_for_session(intruder) == []
    assert await repo.delete(doc.id, intruder) is False  # cannot delete another session's doc
    assert await repo.delete(doc.id, owner) is True


@pytest.mark.asyncio
async def test_chunk_upsert_is_idempotent():
    docs = MemoryDocumentRepository()
    chunks = MemoryChunkRepository(docs)
    doc = make_doc()
    await docs.create(doc)

    batch = [
        Chunk(document_id=doc.id, page_number=1, chunk_index=0, content="a", token_count=1),
        Chunk(document_id=doc.id, page_number=1, chunk_index=1, content="b", token_count=1),
    ]
    assert await chunks.upsert_many(batch) == 2
    # Retry the same page (e.g. after a 429) — same positions, new UUIDs.
    retry = [
        Chunk(document_id=doc.id, page_number=1, chunk_index=0, content="a", token_count=1),
        Chunk(document_id=doc.id, page_number=1, chunk_index=1, content="b", token_count=1),
    ]
    assert await chunks.upsert_many(retry) == 0
    assert await chunks.count_for_document(doc.id) == 2


@pytest.mark.asyncio
async def test_match_respects_session_status_threshold_and_filter():
    docs = MemoryDocumentRepository()
    chunks = MemoryChunkRepository(docs)
    session = uuid4()

    ready_doc = make_doc(session_id=session)
    processing_doc = make_doc(session_id=session, status=DocumentStatus.processing)
    other_session_doc = make_doc()
    for d in (ready_doc, processing_doc, other_session_doc):
        await docs.create(d)

    emb_hit = [1.0, 0.0, 0.0]
    emb_far = [0.0, 1.0, 0.0]
    await chunks.upsert_many(
        [
            Chunk(document_id=ready_doc.id, page_number=1, chunk_index=0, content="hit",
                  token_count=1, embedding=emb_hit),
            Chunk(document_id=ready_doc.id, page_number=2, chunk_index=0, content="far",
                  token_count=1, embedding=emb_far),
            Chunk(document_id=processing_doc.id, page_number=1, chunk_index=0, content="not ready",
                  token_count=1, embedding=emb_hit),
            Chunk(document_id=other_session_doc.id, page_number=1, chunk_index=0, content="leak",
                  token_count=1, embedding=emb_hit),
        ]
    )

    results = await chunks.match([1.0, 0.0, 0.0], 8, 0.35, session)
    contents = [r.content for r in results]
    assert contents == ["hit"]  # threshold excludes orthogonal; status + session excluded others

    # Document filter narrows further
    results = await chunks.match([1.0, 0.0, 0.0], 8, 0.35, session, [processing_doc.id])
    assert results == []


@pytest.mark.asyncio
async def test_conversation_isolation_and_citations():
    repo = MemoryConversationRepository()
    owner = uuid4()
    conv = Conversation(session_id=owner)
    await repo.create(conv)

    assert await repo.get(conv.id, uuid4()) is None
    assert await repo.get(conv.id, owner) is not None

    msg = Message(conversation_id=conv.id, role="assistant", content="hi", grounded=True)
    await repo.add_message(msg)
    await repo.add_citations(msg.id, [{"chunk_id": str(uuid4()), "page_number": 1, "excerpt": "x"}])

    assert len(await repo.list_messages(conv.id)) == 1
    assert len(await repo.list_citations(msg.id)) == 1


@pytest.mark.asyncio
async def test_message_role_validation():
    with pytest.raises(ValueError):
        Message(conversation_id=uuid4(), role="system", content="nope")


@pytest.mark.asyncio
async def test_storage_roundtrip_and_missing_blob():
    storage = MemoryStorageRepository()
    await storage.save("a/b.pdf", b"%PDF-1.4", "application/pdf")
    assert await storage.load("a/b.pdf") == b"%PDF-1.4"
    assert await storage.delete("a/b.pdf") is True
    assert await storage.delete("a/b.pdf") is False
    with pytest.raises(KeyError):
        await storage.load("a/b.pdf")


@pytest.mark.asyncio
async def test_retrieval_log_roundtrip():
    from app.domain.models import RetrievalLog

    repo = MemoryRetrievalLogRepository()
    mid = uuid4()
    await repo.create(
        RetrievalLog(message_id=mid, query="q", top_k=8, threshold=0.35,
                     returned_count=2, max_similarity=0.9, duration_ms=12)
    )
    log = await repo.get_for_message(mid)
    assert log is not None and log.returned_count == 2
    assert await repo.get_for_message(uuid4()) is None


def test_document_size_constraint():
    with pytest.raises(ValueError):
        Document(
            filename="big.pdf", content_type="application/pdf",
            file_size=11 * 1024 * 1024, storage_path="x", session_id=uuid4(),
        )
    with pytest.raises(ValueError):
        Document(
            filename="empty.pdf", content_type="application/pdf",
            file_size=0, storage_path="x", session_id=uuid4(),
        )
