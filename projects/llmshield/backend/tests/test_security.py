from __future__ import annotations

from contextlib import contextmanager

import pytest
from fastapi.testclient import TestClient

from app.auth import Scope, authenticate
from app.main import create_app, validate_live_configuration
from app.providers import DeterministicProvider, FallbackProvider
from app.rate_limit import MemoryRateLimiter, PostgresRateLimiter, RateLimitExceeded
from app.repository import MemoryLogRepository
from app.service import GatewayService


def _service() -> GatewayService:
    return GatewayService(
        provider=FallbackProvider(DeterministicProvider()),
        repository=MemoryLogRepository(),
    )


def _required_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AUTH_MODE", "required")
    monkeypatch.setenv("GATEWAY_API_KEYS", "g" * 32)
    monkeypatch.setenv("TELEMETRY_API_KEYS", "t" * 32)
    monkeypatch.setenv("AUTH_FINGERPRINT_KEY", "f" * 32)


def test_required_auth_rejects_missing_and_invalid_gateway_tokens(monkeypatch):
    _required_auth(monkeypatch)
    api = TestClient(create_app(_service(), MemoryRateLimiter()))

    missing = api.post("/api/gateway", json={"prompt": "Explain RAG"})
    invalid = api.post(
        "/api/gateway",
        headers={"Authorization": "Bearer wrong"},
        json={"prompt": "Explain RAG"},
    )

    assert missing.status_code == 401
    assert missing.headers["www-authenticate"] == "Bearer"
    assert invalid.status_code == 401


def test_gateway_token_cannot_read_private_telemetry(monkeypatch):
    _required_auth(monkeypatch)
    api = TestClient(create_app(_service(), MemoryRateLimiter()))
    gateway_headers = {"Authorization": f"Bearer {'g' * 32}"}
    telemetry_headers = {"Authorization": f"Bearer {'t' * 32}"}

    assert api.post(
        "/api/gateway", headers=gateway_headers, json={"prompt": "Explain RAG"}
    ).status_code == 200
    assert api.get("/api/logs", headers=gateway_headers).status_code == 403
    assert api.get("/api/stats", headers=gateway_headers).status_code == 403
    assert api.get("/api/logs", headers=telemetry_headers).status_code == 200
    assert api.get("/api/stats", headers=telemetry_headers).status_code == 200


def test_rate_limit_is_scoped_and_returns_retry_after(monkeypatch):
    _required_auth(monkeypatch)
    api = TestClient(create_app(_service(), MemoryRateLimiter(limit=1, window_seconds=60)))
    headers = {"Authorization": f"Bearer {'g' * 32}"}

    first = api.post("/api/gateway", headers=headers, json={"prompt": "Explain RAG"})
    limited = api.post("/api/gateway", headers=headers, json={"prompt": "Explain RAG"})

    assert first.status_code == 200
    assert first.headers["x-request-id"]
    assert limited.status_code == 429
    assert int(limited.headers["retry-after"]) > 0
    assert limited.headers["x-request-id"]


def test_authentication_principal_never_contains_raw_token(monkeypatch):
    _required_auth(monkeypatch)
    token = "g" * 32

    principal = authenticate(f"Bearer {token}", Scope.GATEWAY)

    assert principal.principal_id.startswith("key:")
    assert token not in principal.principal_id


def test_live_configuration_requires_database_auth_and_secrets(monkeypatch):
    monkeypatch.setenv("PROVIDER_MODE", "live")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        validate_live_configuration()

    monkeypatch.setenv("DATABASE_URL", "postgresql://example.invalid/db")
    monkeypatch.setenv("AUTH_MODE", "deterministic")
    with pytest.raises(RuntimeError, match="AUTH_MODE"):
        validate_live_configuration()

    monkeypatch.setenv("AUTH_MODE", "required")
    with pytest.raises(RuntimeError, match="GATEWAY_API_KEYS"):
        validate_live_configuration()


@contextmanager
def _context(value):
    yield value


class _FakeCursor:
    def __init__(self, count: int):
        self.count = count
        self.executions: list[tuple[str, dict | None]] = []

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def execute(self, statement, parameters=None):
        self.executions.append((statement, parameters))

    def fetchone(self):
        return self.count, 9


class _FakeConnection:
    def __init__(self, count: int):
        self.cursor_instance = _FakeCursor(count)

    def cursor(self):
        return self.cursor_instance

    def transaction(self):
        return _context(self)


class _FakePool:
    def __init__(self, count: int):
        self.connection_instance = _FakeConnection(count)

    def connection(self):
        return _context(self.connection_instance)


def test_postgres_limiter_uses_atomic_bucket_and_capability_role(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_HASH_KEY", "r" * 32)
    pool = _FakePool(count=2)
    limiter = PostgresRateLimiter(
        "postgresql://unused", pool=pool, limit=2, window_seconds=60
    )

    limiter.check("principal-a", "203.0.113.5")

    executions = pool.connection_instance.cursor_instance.executions
    assert executions[0] == ("SET LOCAL ROLE llmshield_rate_limiter", None)
    assert "ON CONFLICT (bucket_key, window_start) DO UPDATE" in executions[1][0]
    assert len(executions[1][1]["bucket_key"]) == 48


def test_postgres_limiter_returns_retry_after_when_exceeded(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_HASH_KEY", "r" * 32)
    limiter = PostgresRateLimiter(
        "postgresql://unused", pool=_FakePool(count=3), limit=2, window_seconds=60
    )

    with pytest.raises(RateLimitExceeded) as error:
        limiter.check("principal-a", "203.0.113.5")

    assert error.value.retry_after_seconds == 9
