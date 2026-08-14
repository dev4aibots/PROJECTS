from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


Verdict = Literal["PASS", "WARN", "BLOCK"]
SecurityStatus = Literal["safe", "warned", "blocked", "error"]


class GatewayRequest(BaseModel):
    prompt: str = Field(max_length=8001)
    system_prompt: str | None = Field(default=None, max_length=4000)
    max_tokens: int = Field(default=256, ge=1, le=2048)


class GuardCheck(BaseModel):
    name: str
    verdict: Verdict
    detail: str
    stage: Literal["input", "output"] = "input"


class Redaction(BaseModel):
    type: str
    replacement: str


class ProviderResult(BaseModel):
    text: str
    provider: str
    token_usage: int | None = None


class GatewayEnvelope(BaseModel):
    answer: str | None
    security_status: SecurityStatus
    checks: list[GuardCheck]
    redactions: list[Redaction] = Field(default_factory=list)
    provider: str | None = None
    fallback_used: bool = False
    latency_ms: int
    trace_id: str
    token_usage: int | None = None
    truncated: bool = False
    error_code: str | None = None


class RequestLog(BaseModel):
    id: str
    prompt_sha256: str
    security_status: SecurityStatus
    blocked_by: list[str]
    provider: str | None
    fallback_used: bool
    latency_ms: int
    token_usage: int | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Stats(BaseModel):
    total: int = 0
    blocked_pct: float = 0
    warn_pct: float = 0
    fallback_pct: float = 0
    p50_latency_ms: int = 0
    p95_latency_ms: int = 0
