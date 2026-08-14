"""Live provider tests over httpx.MockTransport — no network, no secrets.

These verify the error-translation boundary: HTTP failures and malformed
bodies become the app's controlled error types, and valid bodies become
validated LLMAnswerDraft objects.
"""

import json
from uuid import uuid4

import httpx
import pytest

from app.core.errors import (
    MalformedModelOutputError,
    ProviderRateLimitError,
    ProviderUnavailableError,
)
from app.domain.models import RetrievedChunk
from app.providers.live import (
    GeminiChatProvider,
    GeminiEmbeddingProvider,
    GroqChatProvider,
)
from app.providers.prompts import extract_json_object

EVIDENCE = [
    RetrievedChunk(
        chunk_id=uuid4(),
        document_id=uuid4(),
        filename="p.pdf",
        page_number=1,
        chunk_index=0,
        content="Refunds are issued within 30 days.",
        similarity=0.9,
    )
]

GOOD_DRAFT = {
    "answer": "Refunds are issued within 30 days.",
    "citations": [
        {"chunk_id": str(EVIDENCE[0].chunk_id), "page": 1, "excerpt": "within 30 days"}
    ],
}


def groq_transport(status: int, content: str | None = None):
    def handler(request: httpx.Request) -> httpx.Response:
        if status != 200:
            return httpx.Response(status, json={"error": "x"})
        body = {"choices": [{"message": {"content": content or json.dumps(GOOD_DRAFT)}}]}
        return httpx.Response(200, json=body)

    return httpx.MockTransport(handler)


def gemini_transport(status: int, content: str | None = None):
    def handler(request: httpx.Request) -> httpx.Response:
        if status != 200:
            return httpx.Response(status, json={"error": "x"})
        body = {
            "candidates": [
                {"content": {"parts": [{"text": content or json.dumps(GOOD_DRAFT)}]}}
            ]
        }
        return httpx.Response(200, json=body)

    return httpx.MockTransport(handler)


class TestGroq:
    async def test_success_parses_draft(self):
        p = GroqChatProvider("key", transport=groq_transport(200))
        draft = await p.answer("q?", EVIDENCE)
        assert draft.answer == GOOD_DRAFT["answer"]
        assert len(draft.citations) == 1

    async def test_429_becomes_rate_limit(self):
        p = GroqChatProvider("key", transport=groq_transport(429))
        with pytest.raises(ProviderRateLimitError):
            await p.answer("q?", EVIDENCE)

    async def test_500_becomes_unavailable(self):
        p = GroqChatProvider("key", transport=groq_transport(500))
        with pytest.raises(ProviderUnavailableError):
            await p.answer("q?", EVIDENCE)

    async def test_network_error_becomes_unavailable(self):
        def boom(request):
            raise httpx.ConnectError("refused")

        p = GroqChatProvider("key", transport=httpx.MockTransport(boom))
        with pytest.raises(ProviderUnavailableError):
            await p.answer("q?", EVIDENCE)

    async def test_non_json_content_becomes_malformed(self):
        p = GroqChatProvider("key", transport=groq_transport(200, "sorry, plain prose"))
        with pytest.raises(MalformedModelOutputError):
            await p.answer("q?", EVIDENCE)

    async def test_markdown_fenced_json_is_tolerated(self):
        fenced = "```json\n" + json.dumps(GOOD_DRAFT) + "\n```"
        p = GroqChatProvider("key", transport=groq_transport(200, fenced))
        draft = await p.answer("q?", EVIDENCE)
        assert draft.answer == GOOD_DRAFT["answer"]


class TestGemini:
    async def test_success_parses_draft(self):
        p = GeminiChatProvider("key", transport=gemini_transport(200))
        draft = await p.answer("q?", EVIDENCE)
        assert draft.answer == GOOD_DRAFT["answer"]

    async def test_429_becomes_rate_limit(self):
        p = GeminiChatProvider("key", transport=gemini_transport(429))
        with pytest.raises(ProviderRateLimitError):
            await p.answer("q?", EVIDENCE)


class TestGeminiEmbeddings:
    async def test_success_returns_ordered_vectors(self):
        def handler(request: httpx.Request) -> httpx.Response:
            n = len(json.loads(request.content)["requests"])
            return httpx.Response(
                200, json={"embeddings": [{"values": [float(i)] * 4} for i in range(n)]}
            )

        p = GeminiEmbeddingProvider("key", transport=httpx.MockTransport(handler))
        vectors = await p.embed_texts(["a", "b", "c"])
        assert len(vectors) == 3
        assert vectors[2] == [2.0, 2.0, 2.0, 2.0]

    async def test_count_mismatch_becomes_malformed(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"embeddings": [{"values": [0.1]}]})

        p = GeminiEmbeddingProvider("key", transport=httpx.MockTransport(handler))
        with pytest.raises(MalformedModelOutputError):
            await p.embed_texts(["a", "b"])


class TestJsonExtraction:
    def test_plain_object(self):
        assert extract_json_object('{"a": 1}') == {"a": 1}

    def test_prose_wrapped_object(self):
        assert extract_json_object('Here you go: {"a": 1} hope that helps') == {"a": 1}

    def test_no_object_raises(self):
        with pytest.raises(ValueError):
            extract_json_object("no json here")
