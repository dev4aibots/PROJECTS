"""Provider protocols: embeddings and structured chat completion.

Implementations:
  - deterministic.py : secret-free, hash-based (tests, local dev)
  - live.py          : Groq (chat) and Gemini (chat + embeddings) over HTTP
  - resilient.py     : retry + fallback decorator over any chat providers

Every implementation must translate raw transport failures into the app's
controlled error types (ProviderRateLimitError / ProviderUnavailableError /
MalformedModelOutputError) — raw HTTP errors never leak upward.
"""

from __future__ import annotations

from typing import Protocol

from ..domain.models import LLMAnswerDraft, RetrievedChunk


class EmbeddingProvider(Protocol):
    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts; result order matches input order."""
        ...

    async def embed_query(self, text: str) -> list[float]:
        """Embed a single retrieval query."""
        ...


class ChatProvider(Protocol):
    name: str

    async def answer(
        self, question: str, evidence: list[RetrievedChunk]
    ) -> LLMAnswerDraft:
        """Produce a structured draft answer grounded ONLY in the evidence.

        Must raise ProviderRateLimitError / ProviderUnavailableError /
        MalformedModelOutputError — never leak raw HTTP errors upward.
        """
        ...
