from __future__ import annotations

import hashlib
import time
import uuid

from .guards.core import injection, pii
from .models import GatewayEnvelope, GatewayRequest, GuardCheck, Redaction, RequestLog
from .observability import NullTraceSink, SafeTrace, TraceSink
from .providers import FallbackProvider, ProviderUnavailable
from .repository import LogRepository


class GatewayFailure(RuntimeError):
    def __init__(self, status_code: int, envelope: GatewayEnvelope):
        super().__init__(envelope.error_code or "gateway_failure")
        self.status_code = status_code
        self.envelope = envelope


class GatewayService:
    def __init__(
        self,
        provider: FallbackProvider,
        repository: LogRepository,
        trace_sink: TraceSink | None = None,
        pii_policy: str = "redact",
        max_output_chars: int = 8000,
    ) -> None:
        if pii_policy not in {"block", "redact", "warn"}:
            raise ValueError("PII policy must be block, redact, or warn")
        self.provider = provider
        self.repository = repository
        self.trace_sink = trace_sink or NullTraceSink()
        self.pii_policy = pii_policy
        self.max_output_chars = max_output_chars

    def process(self, request: GatewayRequest) -> GatewayEnvelope:
        started = time.perf_counter()
        trace = SafeTrace(self.trace_sink)
        checks: list[GuardCheck] = []
        redactions: list[Redaction] = []

        guard_started = time.time()
        length_blocked = not request.prompt.strip() or len(request.prompt) > 8000
        checks.append(GuardCheck(
            name="length", verdict="BLOCK" if length_blocked else "PASS",
            detail="prompt must contain 1–8,000 non-whitespace characters", stage="input",
        ))
        inj = injection(request.prompt)
        checks.append(GuardCheck(**inj, stage="input"))
        input_pii, redacted_prompt = pii(request.prompt)
        pii_verdict = "BLOCK" if input_pii and self.pii_policy == "block" else "WARN" if input_pii else "PASS"
        checks.append(GuardCheck(name="pii_input", verdict=pii_verdict, detail=f"{len(input_pii)} sensitive value(s) detected", stage="input"))
        redactions.extend(Redaction(type=kind, replacement=f"[REDACTED:{kind}]") for kind, _ in input_pii)
        trace.span("input-guards", guard_started, {"verdicts": [check.verdict for check in checks]})

        if any(check.verdict == "BLOCK" for check in checks):
            envelope = self._envelope(started, trace.trace_id, checks, redactions, "blocked")
            self._finalize(request.prompt, envelope)
            trace.finish({"security_status": "blocked", "provider": None})
            return envelope

        provider_prompt = request.prompt if self.pii_policy == "warn" else redacted_prompt
        llm_started = time.time()
        try:
            result, fallback_used = self.provider.complete(provider_prompt, request.system_prompt, request.max_tokens)
            trace.span("llm-call", llm_started, {"provider": result.provider, "fallback_used": fallback_used, "token_usage": result.token_usage})
        except ProviderUnavailable:
            trace.span("llm-call", llm_started, {"error": "providers_unavailable"})
            envelope = self._envelope(started, trace.trace_id, checks, redactions, "error", error_code="providers_unavailable")
            self._finalize(request.prompt, envelope)
            trace.finish({"security_status": "error", "error_code": envelope.error_code})
            raise GatewayFailure(503, envelope)

        output_started = time.time()
        raw_answer = result.text
        if not raw_answer.strip():
            checks.append(GuardCheck(name="output_nonempty", verdict="BLOCK", detail="provider returned an empty completion", stage="output"))
            envelope = self._envelope(
                started, trace.trace_id, checks, redactions, "blocked", provider=result.provider,
                fallback_used=fallback_used, token_usage=result.token_usage, error_code="empty_provider_output",
            )
            trace.span("output-guards", output_started, {"error": "empty_provider_output"})
            self._finalize(request.prompt, envelope)
            trace.finish({"security_status": "blocked", "provider": result.provider})
            raise GatewayFailure(502, envelope)

        truncated = len(raw_answer) > self.max_output_chars
        answer = raw_answer[: self.max_output_chars]
        checks.append(GuardCheck(name="output_nonempty", verdict="PASS", detail="provider returned a non-empty completion", stage="output"))
        checks.append(GuardCheck(
            name="output_size", verdict="WARN" if truncated else "PASS",
            detail=f"completion {'truncated to' if truncated else 'within'} {self.max_output_chars} characters", stage="output",
        ))
        output_pii, redacted_answer = pii(answer)
        checks.append(GuardCheck(name="pii_output", verdict="WARN" if output_pii else "PASS", detail=f"{len(output_pii)} sensitive value(s) redacted", stage="output"))
        redactions.extend(Redaction(type=kind, replacement=f"[REDACTED:{kind}]") for kind, _ in output_pii)
        trace.span("output-guards", output_started, {"truncated": truncated, "pii_count": len(output_pii)})

        status = "warned" if any(check.verdict == "WARN" for check in checks) else "safe"
        envelope = self._envelope(
            started, trace.trace_id, checks, redactions, status, answer=redacted_answer,
            provider=result.provider, fallback_used=fallback_used, token_usage=result.token_usage,
            truncated=truncated,
        )
        self._finalize(request.prompt, envelope)
        trace.finish({"security_status": status, "provider": result.provider, "fallback_used": fallback_used})
        return envelope

    def _envelope(
        self, started: float, trace_id: str, checks: list[GuardCheck], redactions: list[Redaction],
        status: str, answer: str | None = None, provider: str | None = None,
        fallback_used: bool = False, token_usage: int | None = None, truncated: bool = False,
        error_code: str | None = None,
    ) -> GatewayEnvelope:
        return GatewayEnvelope(
            answer=answer, security_status=status, checks=checks, redactions=redactions,
            provider=provider, fallback_used=fallback_used,
            latency_ms=max(0, int((time.perf_counter() - started) * 1000)), trace_id=trace_id,
            token_usage=token_usage, truncated=truncated, error_code=error_code,
        )

    def _finalize(self, prompt: str, envelope: GatewayEnvelope) -> None:
        self.repository.add(RequestLog(
            id=str(uuid.uuid4()), prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest(),
            security_status=envelope.security_status,
            blocked_by=[check.name for check in envelope.checks if check.verdict == "BLOCK"],
            provider=envelope.provider, fallback_used=envelope.fallback_used,
            latency_ms=envelope.latency_ms, token_usage=envelope.token_usage,
        ))
