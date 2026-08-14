from __future__ import annotations

import base64
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Protocol

import httpx

logger = logging.getLogger("llmshield.observability")


class TraceSink(Protocol):
    def submit(self, trace_id: str, started_at: float, spans: list[dict[str, Any]], metadata: dict[str, Any]) -> None: ...


class NullTraceSink:
    def submit(self, trace_id: str, started_at: float, spans: list[dict[str, Any]], metadata: dict[str, Any]) -> None:
        return None


@dataclass
class LangfuseHttpSink:
    public_key: str
    secret_key: str
    host: str = "https://cloud.langfuse.com"
    timeout_seconds: float = 2.0

    def submit(self, trace_id: str, started_at: float, spans: list[dict[str, Any]], metadata: dict[str, Any]) -> None:
        auth = base64.b64encode(f"{self.public_key}:{self.secret_key}".encode()).decode()
        now = time.time()
        batch: list[dict[str, Any]] = [{
            "id": str(uuid.uuid4()),
            "type": "trace-create",
            "timestamp": _iso(now),
            "body": {"id": trace_id, "name": "gateway-request", "timestamp": _iso(started_at), "metadata": metadata},
        }]
        for span in spans:
            batch.append({
                "id": str(uuid.uuid4()),
                "type": "span-create",
                "timestamp": _iso(now),
                "body": {
                    "id": span["id"], "traceId": trace_id, "name": span["name"],
                    "startTime": _iso(span["started_at"]), "endTime": _iso(span["ended_at"]),
                    "metadata": span.get("metadata", {}),
                },
            })
        response = httpx.post(
            f"{self.host.rstrip('/')}/api/public/ingestion",
            headers={"Authorization": f"Basic {auth}"},
            json={"batch": batch}, timeout=self.timeout_seconds,
        )
        response.raise_for_status()


def _iso(timestamp: float) -> str:
    from datetime import datetime, timezone
    return datetime.fromtimestamp(timestamp, timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass
class SafeTrace:
    sink: TraceSink
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    started_at: float = field(default_factory=time.time)
    spans: list[dict[str, Any]] = field(default_factory=list)

    def span(self, name: str, started_at: float, metadata: dict[str, Any] | None = None) -> None:
        self.spans.append({
            "id": str(uuid.uuid4()), "name": name, "started_at": started_at,
            "ended_at": time.time(), "metadata": metadata or {},
        })

    def finish(self, metadata: dict[str, Any]) -> None:
        try:
            self.sink.submit(self.trace_id, self.started_at, self.spans, metadata)
        except Exception as exc:  # tracing is deliberately fail-open
            logger.warning("Trace submission failed: %s", type(exc).__name__)
