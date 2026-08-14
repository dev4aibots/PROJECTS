from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import UUID

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException

from app.auth import IdentityVerifier


USER_ID = UUID("10000000-0000-0000-0000-000000000001")


class StaticJwksClient:
    def __init__(self, key):
        self.key = key

    def get_signing_key_from_jwt(self, _token):
        return SimpleNamespace(key=self.key)


def live_verifier(public_key):
    return IdentityVerifier(
        mode="live",
        issuer="https://project.supabase.co/auth/v1",
        audience="authenticated",
        jwt_client=StaticJwksClient(public_key),
    )


def token(private_key, **overrides):
    now = datetime.now(timezone.utc)
    claims = {
        "sub": str(USER_ID),
        "email": "user@example.test",
        "iss": "https://project.supabase.co/auth/v1",
        "aud": "authenticated",
        "iat": now,
        "exp": now + timedelta(minutes=5),
    }
    claims.update(overrides)
    return jwt.encode(claims, private_key, algorithm="RS256", headers={"kid": "test"})


def test_live_verifier_accepts_valid_signed_claims():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    principal = live_verifier(private_key.public_key()).verify(token(private_key))
    assert principal.user_id == USER_ID
    assert principal.email == "user@example.test"


@pytest.mark.parametrize(
    "overrides",
    [
        {"aud": "wrong"},
        {"iss": "https://attacker.example"},
        {"exp": datetime.now(timezone.utc) - timedelta(seconds=1)},
        {"sub": "not-a-uuid"},
    ],
)
def test_live_verifier_rejects_invalid_claims(overrides):
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    with pytest.raises(HTTPException) as exc:
        live_verifier(private_key.public_key()).verify(token(private_key, **overrides))
    assert exc.value.status_code == 401
    assert exc.value.headers == {"WWW-Authenticate": "Bearer"}


def test_live_mode_requires_issuer_and_bearer_credentials():
    with pytest.raises(RuntimeError):
        IdentityVerifier(mode="live")
    verifier = IdentityVerifier(mode="live", issuer="https://project.supabase.co/auth/v1")
    with pytest.raises(HTTPException) as exc:
        verifier.authenticate(None, None)
    assert exc.value.status_code == 401


def test_local_mode_rejects_malformed_demo_identity():
    verifier = IdentityVerifier(mode="local")
    with pytest.raises(HTTPException) as exc:
        verifier.authenticate(None, "not-a-uuid")
    assert exc.value.status_code == 400
