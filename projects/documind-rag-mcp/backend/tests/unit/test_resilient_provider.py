"""Resilient provider tests: retry policy, fallback chain, error surfacing."""

from uuid import uuid4

import pytest

from app.core.errors import (
    MalformedModelOutputError,
    ProviderRateLimitError,
    ProviderUnavailableError,
)
from app.domain.models import LLMAnswerDraft, RetrievedChunk
from app.providers.deterministic import (
    DeadChatProvider,
    DeterministicChatProvider,
    FlakyChatProvider,
)
from app.providers.resilient import ResilientChatProvider

EVIDENCE = [
    RetrievedChunk(
        chunk_id=uuid4(),
        document_id=uuid4(),
        filename="p.pdf",
        page_number=1,
        chunk_index=0,
        content="Refunds are issued within 30 days of purchase.",
        similarity=0.9,
    )
]


async def no_sleep(_):
    return None


class TestRetry:
    async def test_rate_limit_retried_then_succeeds(self):
        flaky = FlakyChatProvider(failures=2, error=ProviderRateLimitError)
        provider = ResilientChatProvider([flaky], max_retries=2, sleep=no_sleep)
        draft = await provider.answer("refund days?", EVIDENCE)
        assert isinstance(draft, LLMAnswerDraft)
        assert flaky.calls == 3

    async def test_rate_limit_exhausted_moves_to_fallback(self):
        flaky = FlakyChatProvider(failures=99, error=ProviderRateLimitError)
        backup = DeterministicChatProvider()
        provider = ResilientChatProvider([flaky, backup], max_retries=2, sleep=no_sleep)
        draft = await provider.answer("refund days?", EVIDENCE)
        assert draft.citations  # backup produced a real draft
        assert flaky.calls == 3  # initial + 2 retries

    async def test_malformed_output_retried_once_only(self):
        flaky = FlakyChatProvider(failures=1, error=MalformedModelOutputError)
        provider = ResilientChatProvider([flaky], max_retries=2, sleep=no_sleep)
        await provider.answer("refund days?", EVIDENCE)
        assert flaky.calls == 2

    async def test_backoff_delays_grow_exponentially(self):
        delays: list[float] = []

        async def record(delay):
            delays.append(delay)

        flaky = FlakyChatProvider(failures=2, error=ProviderRateLimitError)
        provider = ResilientChatProvider(
            [flaky], max_retries=2, base_delay_s=0.5, sleep=record
        )
        await provider.answer("q?", EVIDENCE)
        assert delays == [0.5, 1.0]


class TestFallbackChain:
    async def test_unavailable_provider_skipped_immediately(self):
        dead = DeadChatProvider()
        backup = DeterministicChatProvider()
        provider = ResilientChatProvider([dead, backup], sleep=no_sleep)
        draft = await provider.answer("refund days?", EVIDENCE)
        assert dead.calls == 1  # no retries on hard unavailability
        assert draft.citations

    async def test_all_providers_dead_raises_controlled_error(self):
        provider = ResilientChatProvider(
            [DeadChatProvider("a"), DeadChatProvider("b")], sleep=no_sleep
        )
        with pytest.raises(ProviderUnavailableError):
            await provider.answer("q?", EVIDENCE)

    async def test_empty_chain_rejected_at_construction(self):
        with pytest.raises(ValueError):
            ResilientChatProvider([])
