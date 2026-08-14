#!/usr/bin/env python3
"""Validate DocuExtract configuration without contacting owner services."""
from __future__ import annotations

import os
from urllib.parse import urlparse


def _https(name: str, value: str, errors: list[str]) -> None:
    if urlparse(value).scheme != "https":
        errors.append(f"{name} must be an HTTPS URL")


def validate(environment: dict[str, str] | None = None) -> list[str]:
    env = environment or dict(os.environ)
    errors: list[str] = []
    app_mode = env.get("APP_MODE", "local").strip().lower()
    auth_mode = env.get("AUTH_MODE", "local").strip().lower()
    extractor_mode = env.get("EXTRACTOR_MODE", "deterministic").strip().lower()
    origins = [item.strip() for item in env.get("CORS_ORIGINS", "").split(",") if item.strip()]

    if app_mode not in {"local", "live"}:
        errors.append("APP_MODE must be local or live")
    if auth_mode not in {"local", "live"}:
        errors.append("AUTH_MODE must be local or live")
    if extractor_mode not in {"deterministic", "live"}:
        errors.append("EXTRACTOR_MODE must be deterministic or live")
    if not origins:
        errors.append("CORS_ORIGINS must contain at least one exact origin")
    if "*" in origins:
        errors.append("CORS_ORIGINS cannot contain a wildcard")

    if app_mode == "live":
        if auth_mode != "live":
            errors.append("AUTH_MODE must be live when APP_MODE=live")
        if extractor_mode != "live":
            errors.append("EXTRACTOR_MODE must be live when APP_MODE=live")
        required = [
            "DATABASE_URL",
            "SUPABASE_URL",
            "SUPABASE_SERVICE_ROLE_KEY",
            "SUPABASE_STORAGE_BUCKET",
            "SUPABASE_JWT_ISSUER",
            "GEMINI_API_KEY",
        ]
        for name in required:
            if not env.get(name, "").strip():
                errors.append(f"{name} is required in live mode")
        if env.get("DATABASE_URL") and urlparse(env["DATABASE_URL"]).scheme not in {
            "postgres",
            "postgresql",
        }:
            errors.append("DATABASE_URL must be a Postgres URL")
        for name in ("SUPABASE_URL", "SUPABASE_JWT_ISSUER"):
            if env.get(name):
                _https(name, env[name], errors)
        for origin in origins:
            _https("CORS_ORIGINS entry", origin, errors)
    elif auth_mode != "local" or extractor_mode != "deterministic":
        errors.append("local APP_MODE requires local auth and deterministic extraction")

    return errors


def main() -> int:
    errors = validate()
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("DocuExtract configuration preflight passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
