"""Per-principal and per-IP abuse limits with a durable Postgres backend."""
from __future__ import annotations

import hashlib
import os
import threading
import time
from contextlib import nullcontext
from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class RateLimitExceeded(Exception):
    retry_after_seconds: int


class RateLimiter(Protocol):
    def check(self, principal_id: str, client_ip: str) -> None: ...


def _bucket_key(principal_id: str, client_ip: str) -> str:
    material = f"{principal_id}\0{client_ip}".encode("utf-8")
    key = os.getenv("RATE_LIMIT_HASH_KEY", "").encode("utf-8")
    return hashlib.blake2b(material, key=key, digest_size=24).hexdigest()


class MemoryRateLimiter:
    """Thread-safe fixed-window limiter for deterministic local operation."""

    def __init__(self, limit: int = 60, window_seconds: int = 60) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self._buckets: dict[str, tuple[int, int]] = {}
        self._lock = threading.Lock()

    def check(self, principal_id: str, client_ip: str) -> None:
        now = int(time.time())
        window_start = now - (now % self.window_seconds)
        key = _bucket_key(principal_id, client_ip)
        with self._lock:
            stored_window, count = self._buckets.get(key, (window_start, 0))
            if stored_window != window_start:
                stored_window, count = window_start, 0
            count += 1
            self._buckets[key] = (stored_window, count)
            if count > self.limit:
                raise RateLimitExceeded(max(1, window_start + self.window_seconds - now))


class PostgresRateLimiter:
    """Atomic fixed-window limiter that survives process restarts."""

    def __init__(
        self,
        database_url: str,
        pool: Any | None = None,
        limit: int = 60,
        window_seconds: int = 60,
    ) -> None:
        if not database_url:
            raise ValueError("DATABASE_URL is required for distributed rate limits")
        if pool is None:
            try:
                from psycopg_pool import ConnectionPool
            except ImportError as exc:  # pragma: no cover - deployment boundary
                raise RuntimeError("Postgres rate limits require psycopg[binary,pool]") from exc
            pool = ConnectionPool(
                conninfo=database_url,
                min_size=0,
                max_size=int(os.getenv("DATABASE_POOL_MAX_SIZE", "3")),
                timeout=float(os.getenv("DATABASE_POOL_TIMEOUT_SECONDS", "5")),
                open=False,
            )
            pool.open(wait=True)
        self._pool = pool
        self.limit = limit
        self.window_seconds = window_seconds

    def check(self, principal_id: str, client_ip: str) -> None:
        parameters = {
            "bucket_key": _bucket_key(principal_id, client_ip),
            "window_seconds": self.window_seconds,
        }
        statement = """
            WITH current_window AS (
                SELECT to_timestamp(
                    floor(extract(epoch FROM now()) / %(window_seconds)s)
                    * %(window_seconds)s
                ) AS starts
            )
            INSERT INTO llmshield_rate_limits (
                bucket_key, window_start, request_count, expires_at
            )
            SELECT bucket_key, starts, 1,
                   starts + make_interval(secs => %(window_seconds)s)
            FROM current_window, (SELECT %(bucket_key)s AS bucket_key) AS key
            ON CONFLICT (bucket_key, window_start) DO UPDATE
              SET request_count = llmshield_rate_limits.request_count + 1
            RETURNING request_count,
              greatest(1, ceil(extract(epoch FROM expires_at - now())))::integer
        """
        with self._pool.connection() as connection:
            transaction = connection.transaction() if hasattr(connection, "transaction") else nullcontext()
            with transaction:
                with connection.cursor() as cursor:
                    cursor.execute("SET LOCAL ROLE llmshield_rate_limiter")
                    cursor.execute(statement, parameters)
                    count, retry_after = cursor.fetchone()
        if count > self.limit:
            raise RateLimitExceeded(retry_after)


def build_rate_limiter(database_url: str | None = None) -> RateLimiter:
    limit = max(1, int(os.getenv("RATE_LIMIT_REQUESTS", "60")))
    window = max(1, int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60")))
    url = database_url if database_url is not None else os.getenv("DATABASE_URL", "")
    if url:
        return PostgresRateLimiter(url, limit=limit, window_seconds=window)
    return MemoryRateLimiter(limit=limit, window_seconds=window)
