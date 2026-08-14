"""Resilient chat provider: bounded retry with backoff, then fallback chain.

Policy per provider:
  - ProviderRateLimitError  -> retry up to `max_retries` with exponential backoff
  - MalformedModelOutputError -> one immediate retry (models are often
    transiently sloppy), then move to the next provider
  - ProviderUnavailableError -> move to the next provider immediately

If every provider in the chain is exhausted, the LAST controlled error is
re-raised so the API layer can return a truthful 5xx with a stable code.
"""

from __future__ import annotations

import asyncio

from ..core.errors import (
    AppError,
    MalformedModelOutputError,
    ProviderRateLimitError,
    ProviderUnavailableError,
)
from ..domain.models import LLMAnswerDraft, RetrievedChunk
from .protocols import ChatProvider


class ResilientChatProvider:
    name = "resilient"

    def __init__(
        self,
        providers: list[ChatProvider],
        max_retries: int = 2,
        base_delay_s: float = 0.5,
        sleep=asyncio.sleep,
    ) -> None:
        if not providers:
            raise ValueError("ResilientChatProvider requires at least one provider")
        self._providers = providers
        self._max_retries = max_retries
        self._base_delay_s = base_delay_s
        self._sleep = sleep

    async def answer(
        self, question: str, evidence: list[RetrievedChunk]
    ) -> LLMAnswerDraft:
        last_error: AppError = ProviderUnavailableError()
        for provider in self._providers:
            rate_limit_attempts = 0
            malformed_attempts = 0
            while True:
                try:
                    return await provider.answer(question, evidence)
                except ProviderRateLimitError as e:
                    last_error = e
                    rate_limit_attempts += 1
                    if rate_limit_attempts > self._max_retries:
                        break  # give up on this provider, try the next
                    await self._sleep(self._base_delay_s * (2 ** (rate_limit_attempts - 1)))
                except MalformedModelOutputError as e:
                    last_error = e
                    malformed_attempts += 1
                    if malformed_attempts > 1:
                        break  # one retry only, then next provider
                except ProviderUnavailableError as e:
                    last_error = e
                    break  # next provider immediately
        raise last_error
