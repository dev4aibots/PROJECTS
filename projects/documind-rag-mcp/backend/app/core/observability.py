"""Best-effort observability adapters.

Telemetry is deliberately outside the answer path: failures are swallowed so
an unavailable tracing vendor can never break document Q&A.
"""
from __future__ import annotations

import base64
from typing import Protocol

import httpx


class EventObserver(Protocol):
    async def emit(self, name: str, metadata: dict) -> None: ...


class NoopObserver:
    async def emit(self, name: str, metadata: dict) -> None:
        return None


class LangfuseObserver:
    """Minimal Langfuse ingestion client with no SDK/runtime coupling."""

    def __init__(self, public_key: str, secret_key: str, host: str) -> None:
        self._url = f"{host.rstrip('/')}/api/public/ingestion"
        token = base64.b64encode(f"{public_key}:{secret_key}".encode()).decode()
        self._headers = {"Authorization": f"Basic {token}"}

    async def emit(self, name: str, metadata: dict) -> None:
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                await client.post(
                    self._url,
                    headers=self._headers,
                    json={"batch": [{"type": "event-create", "body": {"name": name, "metadata": metadata}}]},
                )
        except Exception:
            return None
