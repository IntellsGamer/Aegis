"""Password hashing built on top of passlib (bcrypt)."""
from __future__ import annotations

from passlib.context import CryptContext

from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Passlib 1.7.4+ raises a warning when rounds are passed per-call;
# we configure bcrypt defaults globally instead.
pwd_context.update(bcrypt__rounds=settings.bcrypt_rounds)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return pwd_context.verify(plain, hashed)
    except (ValueError, TypeError):
        return False
