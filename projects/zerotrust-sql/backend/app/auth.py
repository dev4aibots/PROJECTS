"""Scoped bearer authentication for query and private audit routes.

Local deterministic mode remains credential-free. Live deployments must set
``AUTH_MODE=required`` and provide independent query/audit bearer tokens. Token
values are compared in constant time and never returned or persisted.
"""
from __future__ import annotations

import hashlib
import hmac
import os
from dataclasses import dataclass
from enum import Enum

from fastapi import Header, HTTPException


class Scope(str, Enum):
    QUERY = "query"
    AUDIT = "audit"


@dataclass(frozen=True)
class Principal:
    principal_id: str
    scopes: frozenset[Scope]

    def allows(self, scope: Scope) -> bool:
        return scope in self.scopes


def _configured_tokens() -> list[tuple[str, frozenset[Scope]]]:
    tokens: list[tuple[str, frozenset[Scope]]] = []
    for value in os.getenv("QUERY_API_KEYS", "").split(","):
        if value.strip():
            tokens.append((value.strip(), frozenset({Scope.QUERY})))
    for value in os.getenv("AUDIT_API_KEYS", "").split(","):
        if value.strip():
            tokens.append((value.strip(), frozenset({Scope.QUERY, Scope.AUDIT})))
    return tokens


def _token_fingerprint(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()[:16]


def authenticate(authorization: str | None, required_scope: Scope) -> Principal:
    """Authenticate one request without leaking whether a token exists."""
    if os.getenv("AUTH_MODE", "deterministic").lower() == "deterministic":
        return Principal("local-demo", frozenset({Scope.QUERY, Scope.AUDIT}))

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


def require_query_principal(
    authorization: str | None = Header(default=None),
) -> Principal:
    return authenticate(authorization, Scope.QUERY)


def require_audit_principal(
    authorization: str | None = Header(default=None),
) -> Principal:
    return authenticate(authorization, Scope.AUDIT)
