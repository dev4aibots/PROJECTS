"""Live HTTP providers: Groq (chat) and Gemini (chat + embeddings).

All raw HTTP failures are translated into the app's controlled error types
at this boundary. These classes are exercised in tests via httpx.MockTransport;
real network calls happen only when API keys are configured.
"""

from __future__ import annotations

import httpx
from pydantic import ValidationError

from ..core.errors import (
    MalformedModelOutputError,
    ProviderRateLimitError,
    ProviderUnavailableError,
)
from ..domain.models import LLMAnswerDraft, RetrievedChunk
from .prompts import SYSTEM_PROMPT, build_user_prompt, extract_json_object

_TIMEOUT = httpx.Timeout(30.0, connect=10.0)


def _classify_status(status: int) -> None:
    """Raise the controlled error type for a non-2xx provider status."""
    if status == 429:
        raise ProviderRateLimitError()
    if status >= 500:
        raise ProviderUnavailableError()
    if status >= 400:
        raise ProviderUnavailableError(f"Provider rejected the request (HTTP {status}).")


def _draft_from_raw(raw_text: str) -> LLMAnswerDraft:
    try:
        obj = extract_json_object(raw_text)
        return LLMAnswerDraft.model_validate(obj)
    except (ValueError, ValidationError):
        raise MalformedModelOutputError() from None


class GroqChatProvider:
    """Groq OpenAI-compatible chat completions."""

    name = "groq"

    def __init__(
        self,
        api_key: str,
        model: str = "llama-3.3-70b-versatile",
        base_url: str = "https://api.groq.com/openai/v1",
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._transport = transport

    async def answer(
        self, question: str, evidence: list[RetrievedChunk]
    ) -> LLMAnswerDraft:
        payload = {
            "model": self._model,
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_user_prompt(question, evidence)},
            ],
        }
        try:
            async with httpx.AsyncClient(
                timeout=_TIMEOUT, transport=self._transport
            ) as client:
                resp = await client.post(
                    f"{self._base_url}/chat/completions",
                    json=payload,
                    headers={"Authorization": f"Bearer {self._api_key}"},
                )
        except httpx.HTTPError:
            raise ProviderUnavailableError() from None

        _classify_status(resp.status_code)
        try:
            raw = resp.json()["choices"][0]["message"]["content"]
        except (KeyError, IndexError, ValueError):
            raise MalformedModelOutputError() from None
        return _draft_from_raw(raw)


class GeminiChatProvider:
    """Gemini generateContent chat."""

    name = "gemini"

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-2.0-flash",
        base_url: str = "https://generativelanguage.googleapis.com/v1beta",
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._transport = transport

    async def answer(
        self, question: str, evidence: list[RetrievedChunk]
    ) -> LLMAnswerDraft:
        payload = {
            "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
            "contents": [
                {"role": "user", "parts": [{"text": build_user_prompt(question, evidence)}]}
            ],
            "generationConfig": {
                "temperature": 0,
                "responseMimeType": "application/json",
            },
        }
        try:
            async with httpx.AsyncClient(
                timeout=_TIMEOUT, transport=self._transport
            ) as client:
                resp = await client.post(
                    f"{self._base_url}/models/{self._model}:generateContent",
                    json=payload,
                    headers={"x-goog-api-key": self._api_key},
                )
        except httpx.HTTPError:
            raise ProviderUnavailableError() from None

        _classify_status(resp.status_code)
        try:
            raw = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, ValueError):
            raise MalformedModelOutputError() from None
        return _draft_from_raw(raw)


class GeminiEmbeddingProvider:
    """Gemini batch embeddings."""

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-embedding-001",
        dimensions: int = 768,
        base_url: str = "https://generativelanguage.googleapis.com/v1beta",
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._dimensions = dimensions
        self._base_url = base_url.rstrip("/")
        self._transport = transport

    async def embed_texts(self, texts: list[float] | list[str]) -> list[list[float]]:
        payload = {
            "requests": [
                {
                    "model": f"models/{self._model}",
                    "content": {"parts": [{"text": t}]},
                    "outputDimensionality": self._dimensions,
                }
                for t in texts
            ]
        }
        try:
            async with httpx.AsyncClient(
                timeout=_TIMEOUT, transport=self._transport
            ) as client:
                resp = await client.post(
                    f"{self._base_url}/models/{self._model}:batchEmbedContents",
                    json=payload,
                    headers={"x-goog-api-key": self._api_key},
                )
        except httpx.HTTPError:
            raise ProviderUnavailableError() from None

        _classify_status(resp.status_code)
        try:
            embeddings = [e["values"] for e in resp.json()["embeddings"]]
        except (KeyError, ValueError):
            raise MalformedModelOutputError() from None
        if len(embeddings) != len(texts):
            raise MalformedModelOutputError()
        return embeddings

    async def embed_query(self, text: str) -> list[float]:
        return (await self.embed_texts([text]))[0]
