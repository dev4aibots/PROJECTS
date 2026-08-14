#!/usr/bin/env python3
"""Fail-closed owner preflight for a live ZeroTrust SQL deployment."""
from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from app.database import PostgresDatabase  # noqa: E402


def _required(name: str, minimum_length: int = 1) -> str:
    value = os.getenv(name, "").strip()
    if len(value) < minimum_length:
        raise RuntimeError(f"{name} must be configured with at least {minimum_length} characters")
    return value


def main() -> int:
    database_url = _required("DATABASE_URL")
    if os.getenv("AUTH_MODE", "").lower() != "required":
        raise RuntimeError("AUTH_MODE must be required in live mode")
    _required("QUERY_API_KEYS", 32)
    _required("AUDIT_API_KEYS", 32)
    _required("AUDIT_HASH_KEY", 32)
    _required("RATE_LIMIT_HASH_KEY", 32)

    database = PostgresDatabase(database_url)
    result = database.preflight()
    safe = database.execute("SELECT id FROM customers ORDER BY id LIMIT 1")
    if safe["row_count"] > 1:
        raise RuntimeError("restricted query returned more rows than requested")

    try:
        database.execute("SELECT secret FROM internal_credentials LIMIT 1")
    except PermissionError:
        pass
    else:
        raise RuntimeError("nl_query_ro can read the prohibited decoy table")

    try:
        database.execute("DELETE FROM customers WHERE id = -1")
    except Exception:
        pass
    else:
        raise RuntimeError("restricted transaction unexpectedly permitted a write")

    roles = ", ".join(sorted(result["role_memberships"]))
    print(f"PASS live database preflight for configured user; roles: {roles}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
