"""REST contract tests over the real FastAPI stack and in-memory adapters."""

from uuid import uuid4

import httpx
import pytest

from app.core.wiring import Container
from app.main import create_app
from app.providers.deterministic import DeterministicChatProvider, DeterministicEmbeddingProvider
from app.repositories.memory import (
    MemoryChunkRepository,
    MemoryConversationRepository,
    MemoryDocumentRepository,
    MemoryRetrievalLogRepository,
    MemoryStorageRepository,
)
from app.services.chat import ChatService
from app.services.documents import DocumentService
from tests.helpers import make_pdf


@pytest.fixture
def api_world():
    documents = MemoryDocumentRepository()
    chunks = MemoryChunkRepository(documents)
    conversations = MemoryConversationRepository()
    logs = MemoryRetrievalLogRepository()
    storage = MemoryStorageRepository()
    embeddings = DeterministicEmbeddingProvider(256)
    container = Container(
        DocumentService(documents, chunks, storage, embeddings, pages_per_batch=1),
        ChatService(
            conversations,
            chunks,
            logs,
            embeddings,
            DeterministicChatProvider(),
            similarity_threshold=0.05,
        ),
        logs,
        "memory",
        "deterministic",
    )
    return create_app(container)


@pytest.fixture
async def client(api_world):
    transport = httpx.ASGITransport(app=api_world)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as value:
        yield value


async def upload_and_process(client: httpx.AsyncClient, session: str) -> dict:
    uploaded = await client.post(
        "/api/documents/upload",
        headers={"X-Session-ID": session},
        files={"file": ("policy.pdf", make_pdf(["Refund requests are accepted within 30 days."]), "application/pdf")},
    )
    assert uploaded.status_code == 201, uploaded.text
    document = uploaded.json()
    processed = await client.post(
        f"/api/documents/{document['id']}/process",
        headers={"X-Session-ID": session},
    )
    assert processed.status_code == 200
    assert processed.json()["done"] is True
    return processed.json()


async def test_health_discloses_modes_not_secrets(client):
    response = await client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "persistence": "memory",
        "llm": "deterministic",
        "live_integrations_configured": False,
    }


async def test_upload_process_list_chat_history_and_retrieval(client):
    session = str(uuid4())
    document = await upload_and_process(client, session)

    listed = await client.get("/api/documents", headers={"X-Session-ID": session})
    assert [item["id"] for item in listed.json()] == [document["id"]]

    answer = await client.post(
        "/api/chat",
        headers={"X-Session-ID": session},
        json={"question": "What is the refund period?", "document_ids": [document["id"]]},
    )
    assert answer.status_code == 200, answer.text
    payload = answer.json()
    assert payload["result"]["grounded"] is True
    assert payload["result"]["citations"][0]["page"] == 1

    history = await client.get(
        f"/api/conversations/{payload['conversation_id']}",
        headers={"X-Session-ID": session},
    )
    assert [message["role"] for message in history.json()["messages"]] == ["user", "assistant"]

    retrieval = await client.get(
        f"/api/retrieval/{payload['message_id']}",
        headers={"X-Session-ID": session},
    )
    assert retrieval.status_code == 200
    assert retrieval.json()["returned_count"] >= 1


async def test_no_evidence_is_a_safe_200_refusal(client):
    session = str(uuid4())
    response = await client.post(
        "/api/chat",
        headers={"X-Session-ID": session},
        json={"question": "What is the refund period?"},
    )
    assert response.status_code == 200
    assert response.json()["result"]["grounded"] is False
    assert response.json()["result"]["citations"] == []


async def test_cross_session_resources_are_not_found(client):
    owner = str(uuid4())
    stranger = str(uuid4())
    document = await upload_and_process(client, owner)
    response = await client.delete(
        f"/api/documents/{document['id']}", headers={"X-Session-ID": stranger}
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


async def test_request_validation_uses_stable_error_shape(client):
    response = await client.get("/api/documents", headers={"X-Session-ID": "not-a-uuid"})
    assert response.status_code == 422
    assert response.json() == {
        "error": {
            "code": "request_validation_error",
            "message": "The request is missing or contains invalid fields.",
        }
    }


async def test_spoofed_pdf_returns_controlled_400(client):
    response = await client.post(
        "/api/documents/upload",
        headers={"X-Session-ID": str(uuid4())},
        files={"file": ("fake.pdf", b"not a pdf", "application/pdf")},
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "validation_error"
