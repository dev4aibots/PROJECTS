#!/usr/bin/env python3
"""Fail-closed owner preflight for a live LLMShield deployment."""
from __future__ import annotations

import os


def _required(name: str, minimum_length: int = 1) -> str:
    value = os.getenv(name, "").strip()
    if len(value) < minimum_length:
        raise RuntimeError(f"{name} must be configured with at least {minimum_length} characters")
    return value


def main() -> int:
    database_url = _required("DATABASE_URL")
    if os.getenv("PROVIDER_MODE", "").lower() != "live":
        raise RuntimeError("PROVIDER_MODE must be live")
    if not os.getenv("GROQ_API_KEY", "").strip() and not os.getenv("GEMINI_API_KEY", "").strip():
        raise RuntimeError("GROQ_API_KEY or GEMINI_API_KEY must be configured")
    if os.getenv("AUTH_MODE", "").lower() != "required":
        raise RuntimeError("AUTH_MODE must be required")
    for name in (
        "GATEWAY_API_KEYS",
        "TELEMETRY_API_KEYS",
        "AUTH_FINGERPRINT_KEY",
        "RATE_LIMIT_HASH_KEY",
    ):
        _required(name, 32)

    try:
        import psycopg
    except ImportError as exc:
        raise RuntimeError("install requirements-dev.txt before running preflight") from exc

    with psycopg.connect(database_url) as connection, connection.cursor() as cursor:
        cursor.execute(
            """SELECT r.rolname
               FROM pg_roles r
               WHERE pg_has_role(current_user, r.oid, 'MEMBER')
                 AND r.rolname IN ('llmshield_log_writer', 'llmshield_rate_limiter')"""
        )
        roles = {row[0] for row in cursor.fetchall()}
        expected = {"llmshield_log_writer", "llmshield_rate_limiter"}
        if roles != expected:
            raise RuntimeError(f"database login is missing capability roles: {sorted(expected - roles)}")
        cursor.execute("SET LOCAL ROLE llmshield_log_writer")
        cursor.execute("SELECT COUNT(*) FROM request_logs")
        cursor.execute("RESET ROLE")
        cursor.execute("SET LOCAL ROLE llmshield_rate_limiter")
        cursor.execute("SELECT COUNT(*) FROM llmshield_rate_limits")

    print("PASS live preflight: configuration, migrations, and capability roles")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
