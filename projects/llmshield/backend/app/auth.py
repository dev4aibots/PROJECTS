"""Scoped bearer authentication for gateway and private telemetry routes."""
from __future__ import annotations

import hashlib
import hmac
import os
from dataclasses import dataclass
from enum import Enum

from fastapi import Header, HTTPException


class Scope(str, Enum):
    GATEWAY = "gateway"
    TELEMETRY = "telemetry"


@dataclass(frozen=True)
class Principal:
    principal_id: str
    scopes: frozenset[Scope]


def _configured_tokens() -> list[tuple[str, frozenset[Scope]]]:
    tokens: list[tuple[str, frozenset[Scope]]] = []
    for value in os.getenv("GATEWAY_API_KEYS", "").split(","):
        if value.strip():
            tokens.append((value.strip(), frozenset({Scope.GATEWAY})))
    for value in os.getenv("TELEMETRY_API_KEYS", "").split(","):
        if value.strip():
            tokens.append((value.strip(), frozenset({Scope.GATEWAY, Scope.TELEMETRY})))
    return tokens


def _token_fingerprint(token: str) -> str:
    key = os.getenv("AUTH_FINGERPRINT_KEY", "").encode("utf-8")
    return hashlib.blake2b(token.encode("utf-8"), key=key, digest_size=12).hexdigest()


def authenticate(authorization: str | None, required_scope: Scope) -> Principal:
    """Authenticate without exposing whether a supplied token exists."""
    if os.getenv("AUTH_MODE", "deterministic").lower() == "deterministic":
        return Principal("local-demo", frozenset({Scope.GATEWAY, Scope.TELEMETRY}))

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="valid bearer authentication is required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    candidate = authorization.removeprefix("Bearer ").strip()
    matched_scopes: frozenset[Scope] | None = None
    for token, scopes in _configured_tokens():
        if hmac.compare_digest(candidate, token):
            matched_scopes = scopes
            break
    if matched_scopes is None:
        raise HTTPException(
            status_code=401,
            detail="valid bearer authentication is required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if required_scope not in matched_scopes:
        raise HTTPException(status_code=403, detail="principal lacks the required scope")
    return Principal(f"key:{_token_fingerprint(candidate)}", matched_scopes)


def require_gateway_principal(
    authorization: str | None = Header(default=None),
) -> Principal:
    return authenticate(authorization, Scope.GATEWAY)


def require_telemetry_principal(
    authorization: str | None = Header(default=None),
) -> Principal:
    return authenticate(authorization, Scope.TELEMETRY)
