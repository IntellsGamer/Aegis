"""Authentication and account services.

Raises app.exceptions.APIError subclasses (not framework-specific) so both
the Flask JSON API and server-rendered pages can translate them.
"""
from __future__ import annotations

from datetime import timedelta

from sqlalchemy.orm import Session

from app.config import settings
from app.exceptions import ForbiddenError, NotFoundError, UnauthorizedError, ValidationError
from app.models import User
from app.repositories.user_repo import UserRepository
from app.security.hashing import hash_password, verify_password
from app.security.jwt import (
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_otp_token,
)
from app.utils.time import utcnow


def token_pair(user_id: int) -> dict:
    access = create_access_token(str(user_id))
    refresh = create_refresh_token(str(user_id))
    return {
        "access_token": access,
        "refresh_token": refresh,
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60,
    }


def register(db: Session, email: str, username: str, password: str,
             full_name: str | None) -> User:
    users = UserRepository(db)
    if users.get_by_email(email):
        raise ValidationError("An account with this email already exists", status_code=409)
    if users.get_by_username(username):
        raise ValidationError("This username is already taken", status_code=409)
    return users.create(
        email=email, username=username, hashed_password=hash_password(password),
        full_name=full_name,
    )


def login(db: Session, identifier: str, password: str, ip: str | None,
          user_agent: str | None) -> dict:
    users = UserRepository(db)
    user = users.get_by_email(identifier) or users.get_by_username(identifier)
    if not user or not verify_password(password, user.hashed_password):
        raise UnauthorizedError("Incorrect email/username or password")
    if not user.is_active:
        raise ForbiddenError("This account has been disabled")
    user.last_login = utcnow()
    users.save(user)

    return token_pair(user.id)


def refresh_tokens(db: Session, refresh_token: str) -> dict:
    users = UserRepository(db)
    session_row = users.get_session(refresh_token)
    if not session_row or session_row.revoked or session_row.expires_at < utcnow():
        raise UnauthorizedError("Invalid or expired refresh token")
    payload = decode_token(refresh_token, expected_type="refresh")
    user = users.get(int(payload["sub"]))
    if not user or not user.is_active:
        raise UnauthorizedError("Account unavailable")
    access, _, expires = token_pair(user.id)  # refresh token reused
    return {"access_token": access, "token_type": "bearer", "expires_in": expires}


def logout(db: Session, refresh_token: str) -> None:
    users = UserRepository(db)
    session_row = users.get_session(refresh_token)
    if session_row and not session_row.revoked:
        users.revoke_session(session_row)


def logout_all(db: Session, user_id: int) -> int:
    return UserRepository(db).revoke_all_sessions(user_id)


def change_password(db: Session, user: User, current: str, new: str) -> None:
    if not verify_password(current, user.hashed_password):
        raise ValidationError("Current password is incorrect")
    user.hashed_password = hash_password(new)
    UserRepository(db).save(user)


def reset_request(db: Session, email: str) -> dict:
    users = UserRepository(db)
    user = users.get_by_email(email)
    if not user:
        # Do not reveal whether the email exists
        return {"token": None, "email_enabled": settings.email_enabled}
    token = generate_otp_token(str(user.id), purpose="password_reset")
    return {"token": token, "email_enabled": settings.email_enabled}


def reset_confirm(db: Session, token: str, new_password: str) -> None:
    try:
        payload = decode_token(token)
    except Exception as exc:
        raise ValidationError("Invalid or expired reset token") from exc
    if payload.get("purpose") != "password_reset" or payload.get("type") != "otp":
        raise ValidationError("Invalid reset token")
    users = UserRepository(db)
    user = users.get(int(payload["sub"]))
    if not user:
        raise NotFoundError("User not found")
    user.hashed_password = hash_password(new_password)
    users.save(user)
    users.revoke_all_sessions(user.id)


def verify_email(db: Session, token: str) -> User:
    try:
        payload = decode_token(token)
    except Exception as exc:
        raise ValidationError("Invalid verification token") from exc
    if payload.get("purpose") != "email_verify":
        raise ValidationError("Invalid verification token")
    users = UserRepository(db)
    user = users.get(int(payload["sub"]))
    if not user:
        raise NotFoundError("User not found")
    user.is_verified = True
    users.save(user)
    return user
