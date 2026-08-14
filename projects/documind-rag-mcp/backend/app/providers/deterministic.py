"""Deterministic, secret-free providers for tests and local dev.

The embedding provider hashes token features into a fixed-size vector, so
similar texts (shared vocabulary) get similar vectors — enough signal for
the retrieval pipeline to behave realistically without any API key.

The chat provider answers by copying the single most relevant evidence
sentence and citing the chunk it came from — a well-behaved model. Tests
that need a MISBEHAVING model use the configurable FlakyChatProvider /
FabricatingChatProvider below.
"""

from __future__ import annotations

import hashlib
import math
import re

from ..core.errors import ProviderRateLimitError, ProviderUnavailableError
from ..domain.models import LLMAnswerDraft, RetrievedChunk

_WORD_RE = re.compile(r"[a-z0-9]+")
_STOP_WORDS = {"a", "an", "and", "are", "does", "for", "how", "is", "of", "the", "to", "what", "where", "which", "who"}


class DeterministicEmbeddingProvider:
    """Hash-bucket bag-of-words embeddings. Deterministic, no secrets."""

    def __init__(self, dimensions: int = 768) -> None:
        self.dimensions = dimensions

    def _embed(self, text: str) -> list[float]:
        vec = [0.0] * self.dimensions
        words = _WORD_RE.findall(text.lower())
        for word in words:
            digest = hashlib.sha256(word.encode()).digest()
            bucket = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vec[bucket] += sign
        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0:
            vec = [v / norm for v in vec]
        return vec

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(t) for t in texts]

    async def embed_query(self, text: str) -> list[float]:
        return self._embed(text)


def _normalize_term(word: str) -> str:
    aliases = {"period": "day", "shipping": "ship", "takes": "take"}
    if word.startswith("measur"):
        return "measure"
    if word.startswith("refund"):
        return "refund"
    if word.endswith("ed") and len(word) > 4:
        word = word[:-2]
    elif word.endswith("s") and len(word) > 3:
        word = word[:-1]
    return aliases.get(word, word)


def _terms(text: str) -> set[str]:
    return {_normalize_term(word) for word in _WORD_RE.findall(text.lower()) if word not in _STOP_WORDS}


def _score_sentence(sentence: str, question: str) -> float:
    q_words = _terms(question)
    s_words = _terms(sentence)
    matched = len(q_words & s_words)
    return matched + (matched / len(q_words) if q_words else 0.0)


class DeterministicChatProvider:
    """A well-behaved 'model': answers strictly from evidence with real citations."""

    name = "deterministic"

    async def answer(
        self, question: str, evidence: list[RetrievedChunk]
    ) -> LLMAnswerDraft:
        best_chunk: RetrievedChunk | None = None
        best_sentence = ""
        best_score = -1.0
        for chunk in evidence:
            for sentence in re.split(r"(?<=[.!?])\s+", chunk.content):
                sentence = sentence.strip()
                if len(sentence) < 10:
                    continue
                score = _score_sentence(sentence, question)
                if score > best_score:
                    best_score = score
                    best_sentence = sentence
                    best_chunk = chunk

        if best_chunk is None or best_score < 2.6:
            # No lexical overlap at all: emit an uncited answer; the
            # deterministic citation gate downstream will refuse it.
            return LLMAnswerDraft(answer="I could not determine this.", citations=[])

        return LLMAnswerDraft(
            answer=f"According to the document: {best_sentence}",
            citations=[
                {
                    "chunk_id": str(best_chunk.chunk_id),
                    "document_id": str(best_chunk.document_id),
                    "page": best_chunk.page_number,
                    "excerpt": best_sentence[:200],
                }
            ],
        )


class FlakyChatProvider:
    """Fails N times with a chosen error, then delegates. For resilience tests."""

    def __init__(
        self,
        inner: DeterministicChatProvider | None = None,
        failures: int = 1,
        error: type[Exception] = ProviderRateLimitError,
        name: str = "flaky",
    ) -> None:
        self.inner = inner or DeterministicChatProvider()
        self.failures_remaining = failures
        self.error = error
        self.name = name
        self.calls = 0

    async def answer(
        self, question: str, evidence: list[RetrievedChunk]
    ) -> LLMAnswerDraft:
        self.calls += 1
        if self.failures_remaining > 0:
            self.failures_remaining -= 1
            raise self.error()
        return await self.inner.answer(question, evidence)


class DeadChatProvider:
    """Always unavailable. For fallback-chain tests."""

    def __init__(self, name: str = "dead") -> None:
        self.name = name
        self.calls = 0

    async def answer(
        self, question: str, evidence: list[RetrievedChunk]
    ) -> LLMAnswerDraft:
        self.calls += 1
        raise ProviderUnavailableError()


class FabricatingChatProvider:
    """A hostile 'model' that invents citations. The gate must strip them."""

    name = "fabricator"

    async def answer(
        self, question: str, evidence: list[RetrievedChunk]
    ) -> LLMAnswerDraft:
        return LLMAnswerDraft(
            answer="Absolutely, the document clearly states the sky is green.",
            citations=[
                {
                    "chunk_id": "00000000-0000-0000-0000-000000000000",
                    "page": 999,
                    "excerpt": "the sky is green and pigs fly",
                }
            ],
        )
