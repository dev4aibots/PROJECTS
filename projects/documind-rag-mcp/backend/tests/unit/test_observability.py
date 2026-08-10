"""Observability must report violations without threatening the answer path."""
import httpx
import pytest

from app.core.observability import LangfuseObserver, NoopObserver


@pytest.mark.asyncio
async def test_noop_observer_accepts_events():
    await NoopObserver().emit("citation_violation", {"stripped_count": 1})


@pytest.mark.asyncio
async def test_langfuse_network_failure_is_best_effort(monkeypatch):
    async def fail(*args, **kwargs):
        raise httpx.ConnectError("offline")

    monkeypatch.setattr(httpx.AsyncClient, "post", fail)
    observer = LangfuseObserver("public", "secret", "https://example.invalid")
    await observer.emit("citation_violation", {"stripped_count": 1})
