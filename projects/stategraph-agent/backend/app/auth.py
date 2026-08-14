"""Verified request identity for local demos and Supabase deployments."""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Annotated, Any
from uuid import UUID

from fastapi import Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


DEMO_USER_ID = UUID("00000000-0000-0000-0000-000000000001")
bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class Principal:
    user_id: UUID
    email: str | None = None


class IdentityVerifier:
    """Authenticate locally with an explicit demo header or live with JWKS.

    Live mode never trusts request body/query identity. Signature, issuer,
    audience, expiry and subject are verified before a UUID is returned.
    """

    def __init__(
        self,
        mode: str,
        issuer: str = "",
        audience: str = "authenticated",
        jwks_url: str = "",
        jwt_client: Any | None = None,
    ) -> None:
        if mode not in {"local", "live"}:
            raise RuntimeError("AUTH_MODE must be local or live")
        if mode == "live" and not issuer:
            raise RuntimeError("SUPABASE_JWT_ISSUER is required when AUTH_MODE=live")
        self.mode = mode
        self.issuer = issuer.rstrip("/")
        self.audience = audience
        self.jwks_url = jwks_url or f"{self.issuer}/.well-known/jwks.json"
        self._jwt_client = jwt_client

    @classmethod
    def from_environment(cls) -> "IdentityVerifier":
        mode = os.getenv("AUTH_MODE", os.getenv("APP_MODE", "local")).strip().lower()
        return cls(
            mode=mode,
            issuer=os.getenv("SUPABASE_JWT_ISSUER", ""),
            audience=os.getenv("SUPABASE_JWT_AUDIENCE", "authenticated"),
            jwks_url=os.getenv("SUPABASE_JWKS_URL", ""),
        )

    def _client(self):
        if self._jwt_client is None:
            import jwt
            self._jwt_client = jwt.PyJWKClient(self.jwks_url, cache_keys=True, lifespan=300)
        return self._jwt_client

    def verify(self, token: str) -> Principal:
        try:
            import jwt
            signing_key = self._client().get_signing_key_from_jwt(token)
            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=["ES256", "RS256"],
                audience=self.audience,
                issuer=self.issuer,
                options={"require": ["exp", "iat", "sub", "aud"]},
            )
            return Principal(user_id=UUID(claims["sub"]), email=claims.get("email"))
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "invalid_token"},
                headers={"WWW-Authenticate": "Bearer"},
            ) from exc

    def authenticate(
        self,
        credentials: HTTPAuthorizationCredentials | None,
        demo_user_id: str | None,
    ) -> Principal:
        if self.mode == "local":
            try:
                return Principal(user_id=UUID(demo_user_id) if demo_user_id else DEMO_USER_ID)
            except ValueError as exc:
                raise HTTPException(400, detail={"code": "invalid_demo_user"}) from exc
        if not credentials or credentials.scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "authentication_required"},
                headers={"WWW-Authenticate": "Bearer"},
            )
        return self.verify(credentials.credentials)


auth = IdentityVerifier.from_environment()


async def current_principal(
    credentials: Annotated[HTTPAuthorizationCredentials | None, __import__("fastapi").Depends(bearer)],
    x_demo_user_id: Annotated[str | None, Header(alias="X-Demo-User-Id")] = None,
) -> Principal:
    return auth.authenticate(credentials, x_demo_user_id)
