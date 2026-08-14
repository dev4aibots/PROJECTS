#!/usr/bin/env python3
"""Validate StateGraph deployment configuration without contacting providers."""
from __future__ import annotations

import os
import sys
from collections.abc import Mapping
from urllib.parse import urlparse


def validate(environment: Mapping[str, str]) -> list[str]:
    errors: list[str] = []
    app_mode = environment.get("APP_MODE", "local")
    auth_mode = environment.get("AUTH_MODE", "local")
    if app_mode not in {"local", "live"}:
        errors.append("APP_MODE must be local or live")
    if auth_mode not in {"local", "live"}:
        errors.append("AUTH_MODE must be local or live")
    if app_mode != "live":
        return errors
    if auth_mode != "live":
        errors.append("AUTH_MODE must be live when APP_MODE is live")

    required = ["DATABASE_URL", "SUPABASE_JWT_ISSUER", "TAVILY_API_KEY", "CORS_ORIGINS"]
    errors.extend(f"{name} is required in live mode" for name in required if not environment.get(name))
    if not (environment.get("GROQ_API_KEY") or environment.get("GEMINI_API_KEY")):
        errors.append("at least one model provider key is required in live mode")

    database_url = environment.get("DATABASE_URL", "")
    if database_url and urlparse(database_url).scheme not in {"postgres", "postgresql"}:
        errors.append("DATABASE_URL must use postgres:// or postgresql://")
    issuer = environment.get("SUPABASE_JWT_ISSUER", "")
    if issuer and urlparse(issuer).scheme != "https":
        errors.append("SUPABASE_JWT_ISSUER must use HTTPS")

    origins = [item.strip() for item in environment.get("CORS_ORIGINS", "").split(",") if item.strip()]
    if "*" in origins:
        errors.append("CORS_ORIGINS cannot contain a wildcard")
    for origin in origins:
        parsed = urlparse(origin)
        if parsed.scheme != "https" or not parsed.netloc or parsed.path not in {"", "/"}:
            errors.append(f"CORS origin must be an HTTPS origin without a path: {origin}")
    return errors


def main() -> int:
    errors = validate(os.environ)
    if errors:
        print("StateGraph preflight failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("PASS: StateGraph configuration is internally consistent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
