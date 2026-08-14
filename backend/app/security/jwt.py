"""JWT creation/verification and opaque-token helpers."""
from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Any

import jwt
from jwt import PyJWTError

from app.config import settings


def _secret() -> str:
    if settings.is_production and settings.secret_key.startswith("change-me"):
        raise RuntimeError(
            "AEGIS_SECRET_KEY must be set to a long random value in production."
        )
    return settings.secret_key


def create_access_token(subject: str, extra: dict[str, Any] | None = None) -> str:
    now = datetime.utcnow()
    payload: dict[str, Any] = {
        "sub": subject,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, _secret(), algorithm=settings.jwt_algorithm)


def create_refresh_token(subject: str) -> str:
    now = datetime.utcnow()
    payload = {
        "sub": subject,
        "type": "refresh",
        "jti": secrets.token_urlsafe(24),
        "iat": now,
        "exp": now + timedelta(minutes=settings.refresh_token_expire_minutes),
    }
    return jwt.encode(payload, _secret(), algorithm=settings.jwt_algorithm)


def decode_token(token: str, expected_type: str | None = None) -> dict[str, Any]:
    """Decode and validate a JWT. Raises jwt.PyJWTError on failure."""
    payload = jwt.decode(
        token, _secret(), algorithms=[settings.jwt_algorithm], verify_aud=False
    )
    if expected_type and payload.get("type") != expected_type:
        raise PyJWTError("Unexpected token type")
    return payload


def generate_otp_token(subject: str, purpose: str, minutes: int | None = None) -> str:
    """Signed one-time token for email verification / password reset."""
    minutes = minutes or settings.password_reset_expire_minutes
    now = datetime.utcnow()
    payload = {
        "sub": subject,
        "type": "otp",
        "purpose": purpose,
        "jti": secrets.token_urlsafe(24),
        "iat": now,
        "exp": now + timedelta(minutes=minutes),
    }
    return jwt.encode(payload, _secret(), algorithm=settings.jwt_algorithm)


def hash_opaque(value: str) -> str:
    """Hash of an opaque random token (session / reset / api key)."""
    return hashlib.sha256(value.encode()).hexdigest()


def generate_random_token(entropy: int = 32) -> str:
    return secrets.token_urlsafe(entropy)
