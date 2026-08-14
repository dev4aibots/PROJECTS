"""Privacy-safe audit repositories for deterministic and live operation.

Every request writes exactly one record. Local mode uses a bounded in-memory
repository. Live mode persists append-only metadata in Postgres while raw
questions and SQL remain disabled unless explicitly opted in.
"""
from __future__ import annotations

import hashlib
import hmac
import itertools
import os
import threading
from collections import deque
from contextlib import nullcontext
from datetime import datetime, timezone
from typing import Any, Protocol


class AuditRepository(Protocol):
    def record(self, **values: Any) -> dict[str, Any]: ...
    def recent(self, limit: int = 50) -> list[dict[str, Any]]: ...
    def get(self, entry_id: int) -> dict[str, Any] | None: ...


def _digest(value: str | None) -> str | None:
    if value is None:
        return None
    key = os.getenv("AUDIT_HASH_KEY", "").encode("utf-8")
    payload = value.encode("utf-8")
    return (
        hmac.new(key, payload, hashlib.sha256).hexdigest()
        if key
        else hashlib.sha256(payload).hexdigest()
    )


def _entry(
    *,
    question: str,
    generated_sql: str | None,
    validation_status: str,
    rejection_reason: str | None = None,
    final_sql: str | None = None,
    checks: list | None = None,
    duration_ms: float | None = None,
    row_count: int | None = None,
    model: str | None = None,
    principal_id: str | None = None,
    request_id: str | None = None,
    store_raw_text: bool = True,
) -> dict[str, Any]:
    return {
        "question": question if store_raw_text else None,
        "question_hash": _digest(question),
        "generated_sql": generated_sql if store_raw_text else None,
        "generated_sql_hash": _digest(generated_sql),
        "final_sql": final_sql if store_raw_text else None,
        "final_sql_hash": _digest(final_sql),
        "validation_status": validation_status,
        "rejection_reason": rejection_reason,
        "checks": checks or [],
        "duration_ms": duration_ms,
        "row_count": row_count,
        "model": model,
        "principal_id": principal_id,
        "request_id": request_id,
    }


class AuditLog:
    """Bounded, thread-safe repository for deterministic local mode."""

    def __init__(self, maxlen: int = 500, store_raw_text: bool = True) -> None:
        self._entries: deque[dict[str, Any]] = deque(maxlen=maxlen)
        self._lock = threading.Lock()
        self._next_id = 1
        self._store_raw_text = store_raw_text

    def record(self, **values: Any) -> dict[str, Any]:
        entry = _entry(store_raw_text=self._store_raw_text, **values)
        with self._lock:
            entry.update({
                "id": self._next_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
            })
            self._next_id += 1
            self._entries.appendleft(entry)
            return entry.copy()

    def recent(self, limit: int = 50) -> list[dict[str, Any]]:
        return [entry.copy() for entry in itertools.islice(
            self._entries, max(1, min(limit, 200))
        )]

    def get(self, entry_id: int) -> dict[str, Any] | None:
        entry = next((item for item in self._entries if item["id"] == entry_id), None)
        return entry.copy() if entry else None


class PostgresAuditLog:
    """Append-only Postgres audit repository using ``nl_audit_writer``."""

    _SELECT = """
        SELECT id, question, prompt_hash AS question_hash, generated_sql,
               generated_sql_hash, final_sql, final_sql_hash, validation_status,
               rejection_reason, checks, duration_ms, row_count, model,
               principal_id, request_id, created_at
        FROM query_audit_logs
    """
    _COLUMNS = (
        "id", "question", "question_hash", "generated_sql",
        "generated_sql_hash", "final_sql", "final_sql_hash",
        "validation_status", "rejection_reason", "checks", "duration_ms",
        "row_count", "model", "principal_id", "request_id", "created_at",
    )

    def __init__(
        self,
        database_url: str,
        pool: Any | None = None,
        store_raw_text: bool = False,
    ) -> None:
        if not database_url:
            raise ValueError("DATABASE_URL is required for durable audit mode")
        if pool is None:
            try:
                from psycopg_pool import ConnectionPool
            except ImportError as exc:  # pragma: no cover - deployment config
                raise RuntimeError("Postgres audit requires psycopg[binary,pool]") from exc
            pool = ConnectionPool(
                conninfo=database_url,
                min_size=0,
                max_size=int(os.getenv("DATABASE_POOL_MAX_SIZE", "3")),
                timeout=float(os.getenv("DATABASE_POOL_TIMEOUT_SECONDS", "5")),
                open=False,
            )
            pool.open(wait=True)
        self._pool = pool
        self._store_raw_text = store_raw_text

    @classmethod
    def _row(cls, row: Any) -> dict[str, Any]:
        result = dict(zip(cls._COLUMNS, row, strict=True))
        if result["created_at"] is not None:
            result["created_at"] = result["created_at"].isoformat()
        return result

    def record(self, **values: Any) -> dict[str, Any]:
        entry = _entry(store_raw_text=self._store_raw_text, **values)
        from psycopg.types.json import Jsonb
        parameters = {**entry, "checks": Jsonb(entry["checks"])}
        sql = """
            INSERT INTO query_audit_logs (
                question, prompt_hash, generated_sql, generated_sql_hash,
                final_sql, final_sql_hash, validation_status, rejection_reason,
                checks, duration_ms, row_count, model, principal_id, request_id
            ) VALUES (
                %(question)s, %(question_hash)s, %(generated_sql)s,
                %(generated_sql_hash)s, %(final_sql)s, %(final_sql_hash)s,
                %(validation_status)s, %(rejection_reason)s, %(checks)s,
                %(duration_ms)s, %(row_count)s, %(model)s, %(principal_id)s,
                %(request_id)s
            ) RETURNING id, created_at
        """
        with self._pool.connection() as conn:
            transaction = conn.transaction() if hasattr(conn, "transaction") else nullcontext()
            with transaction:
                with conn.cursor() as cur:
                    cur.execute("SET LOCAL ROLE nl_audit_writer")
                    cur.execute(sql, parameters)
                    entry_id, created_at = cur.fetchone()
        entry.update({"id": entry_id, "created_at": created_at.isoformat()})
        return entry

    def recent(self, limit: int = 50) -> list[dict[str, Any]]:
        bounded = max(1, min(limit, 200))
        with self._pool.connection() as conn:
            transaction = conn.transaction() if hasattr(conn, "transaction") else nullcontext()
            with transaction:
                with conn.cursor() as cur:
                    cur.execute("SET LOCAL ROLE nl_audit_writer")
                    cur.execute(
                        self._SELECT + " ORDER BY id DESC LIMIT %s",
                        (bounded,),
                    )
                    return [self._row(row) for row in cur.fetchall()]

    def get(self, entry_id: int) -> dict[str, Any] | None:
        with self._pool.connection() as conn:
            transaction = conn.transaction() if hasattr(conn, "transaction") else nullcontext()
            with transaction:
                with conn.cursor() as cur:
                    cur.execute("SET LOCAL ROLE nl_audit_writer")
                    cur.execute(self._SELECT + " WHERE id = %s", (entry_id,))
                    row = cur.fetchone()
                    return self._row(row) if row else None


def build_audit_repository(database_url: str | None = None) -> AuditRepository:
    url = database_url if database_url is not None else os.getenv("DATABASE_URL", "")
    if not url:
        return AuditLog()
    store_raw = os.getenv("AUDIT_STORE_RAW_TEXT", "false").lower() == "true"
    return PostgresAuditLog(url, store_raw_text=store_raw)
