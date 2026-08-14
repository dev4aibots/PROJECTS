from contextlib import contextmanager

import pytest

from app.rate_limit import MemoryRateLimiter, PostgresRateLimiter, RateLimitExceeded


@contextmanager
def _context(value):
    yield value


class FakeCursor:
    def __init__(self, count, retry_after=12):
        self.count = count
        self.retry_after = retry_after
        self.executions = []

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def execute(self, statement, parameters=None):
        self.executions.append((statement, parameters))

    def fetchone(self):
        return self.count, self.retry_after


class FakeConnection:
    def __init__(self, count):
        self.cursor_instance = FakeCursor(count)

    def cursor(self):
        return self.cursor_instance

    def transaction(self):
        return _context(self)


class FakePool:
    def __init__(self, count):
        self.connection_instance = FakeConnection(count)

    def connection(self):
        return _context(self.connection_instance)


def test_memory_limiter_is_scoped_by_principal_and_ip():
    limiter = MemoryRateLimiter(limit=1, window_seconds=60)
    limiter.check("principal-a", "127.0.0.1")
    limiter.check("principal-b", "127.0.0.1")
    limiter.check("principal-a", "127.0.0.2")

    with pytest.raises(RateLimitExceeded) as error:
        limiter.check("principal-a", "127.0.0.1")

    assert error.value.retry_after_seconds > 0


def test_postgres_limiter_uses_atomic_bucket_and_capability_role():
    pool = FakePool(count=2)
    limiter = PostgresRateLimiter(
        "postgresql://unused",
        pool=pool,
        limit=2,
        window_seconds=60,
    )

    limiter.check("principal-a", "203.0.113.5")

    executions = pool.connection_instance.cursor_instance.executions
    assert executions[0] == ("SET LOCAL ROLE nl_rate_limiter", None)
    assert "ON CONFLICT (bucket_key, window_start) DO UPDATE" in executions[1][0]
    assert len(executions[1][1]["bucket_key"]) == 48


def test_postgres_limiter_returns_retry_after_when_exceeded():
    pool = FakePool(count=3)
    limiter = PostgresRateLimiter(
        "postgresql://unused",
        pool=pool,
        limit=2,
        window_seconds=60,
    )

    with pytest.raises(RateLimitExceeded) as error:
        limiter.check("principal-a", "203.0.113.5")

    assert error.value.retry_after_seconds == 12
