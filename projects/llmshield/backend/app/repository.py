from __future__ import annotations

import json
import math
import uuid
from threading import Lock
from typing import Protocol

from .models import RequestLog, Stats


class LogRepository(Protocol):
    def add(self, row: RequestLog) -> None: ...

    def recent(self, limit: int) -> list[RequestLog]: ...

    def stats(self) -> Stats: ...


def _percentile(values: list[int], percentile: float) -> int:
    if not values:
        return 0
    ordered = sorted(values)
    index = max(0, math.ceil(percentile * len(ordered)) - 1)
    return ordered[index]


def _stats(rows: list[RequestLog]) -> Stats:
    total = len(rows)
    if not total:
        return Stats()
    percent = lambda count: round(100 * count / total, 1)
    return Stats(
        total=total,
        blocked_pct=percent(sum(row.security_status == "blocked" for row in rows)),
        warn_pct=percent(sum(row.security_status == "warned" for row in rows)),
        fallback_pct=percent(sum(row.fallback_used for row in rows)),
        p50_latency_ms=_percentile([row.latency_ms for row in rows], 0.5),
        p95_latency_ms=_percentile([row.latency_ms for row in rows], 0.95),
    )


class MemoryLogRepository:
    def __init__(self) -> None:
        self._rows: list[RequestLog] = []
        self._lock = Lock()

    def add(self, row: RequestLog) -> None:
        with self._lock:
            self._rows.append(row)

    def recent(self, limit: int) -> list[RequestLog]:
        with self._lock:
            return list(reversed(self._rows[-limit:]))

    def stats(self) -> Stats:
        with self._lock:
            return _stats(list(self._rows))


class PostgresLogRepository:
    """Connection-per-operation adapter suitable for serverless runtimes."""

    def __init__(self, database_url: str) -> None:
        self.database_url = database_url

    def _connect(self):
        try:
            import psycopg
        except ImportError as exc:  # pragma: no cover - deployment dependency boundary
            raise RuntimeError("Install psycopg[binary] to use DATABASE_URL") from exc
        return psycopg.connect(self.database_url)

    def add(self, row: RequestLog) -> None:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """INSERT INTO request_logs
                (id, prompt_sha256, security_status, blocked_by, provider,
                 fallback_used, latency_ms, token_usage, created_at)
                VALUES (%s, %s, %s, %s::jsonb, %s, %s, %s, %s, %s)""",
                (
                    uuid.UUID(row.id), row.prompt_sha256, row.security_status,
                    json.dumps(row.blocked_by), row.provider, row.fallback_used,
                    row.latency_ms, row.token_usage, row.created_at,
                ),
            )

    def recent(self, limit: int) -> list[RequestLog]:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """SELECT id, prompt_sha256, security_status, blocked_by, provider,
                fallback_used, latency_ms, token_usage, created_at
                FROM request_logs ORDER BY created_at DESC LIMIT %s""",
                (limit,),
            )
            return [
                RequestLog(
                    id=str(row[0]), prompt_sha256=row[1], security_status=row[2],
                    blocked_by=row[3], provider=row[4], fallback_used=row[5],
                    latency_ms=row[6], token_usage=row[7], created_at=row[8],
                )
                for row in cursor.fetchall()
            ]

    def stats(self) -> Stats:
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(
                """SELECT COUNT(*),
                COALESCE(100.0 * COUNT(*) FILTER (WHERE security_status='blocked') / NULLIF(COUNT(*),0), 0),
                COALESCE(100.0 * COUNT(*) FILTER (WHERE security_status='warned') / NULLIF(COUNT(*),0), 0),
                COALESCE(100.0 * COUNT(*) FILTER (WHERE fallback_used) / NULLIF(COUNT(*),0), 0),
                COALESCE(percentile_disc(0.5) WITHIN GROUP (ORDER BY latency_ms), 0),
                COALESCE(percentile_disc(0.95) WITHIN GROUP (ORDER BY latency_ms), 0)
                FROM request_logs"""
            )
            row = cursor.fetchone()
            return Stats(total=row[0], blocked_pct=round(float(row[1]), 1), warn_pct=round(float(row[2]), 1), fallback_pct=round(float(row[3]), 1), p50_latency_ms=row[4], p95_latency_ms=row[5])
