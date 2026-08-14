"""Auth API blueprint (JSON) + session management for the web UI."""
from __future__ import annotations

from datetime import timedelta

from flask import Blueprint, jsonify, request, session as flask_session, url_for

from app.config import settings
from app.dependencies import admin_required, current_user, db_session, login_required
from app.exceptions import APIError, UnauthorizedError, ValidationError
from app.repositories.user_repo import UserRepository
from app.schemas.auth import (
    LoginRequest,
    PasswordChangeRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    RegisterRequest,
    VerifyEmailRequest,
)
from app.security.jwt import create_access_token, create_refresh_token
from app.security.sanitize import strip_dangerous_tags
from app.services import auth_service
from app.services.notification_service import send_email
from app.utils.time import utcnow

bp = Blueprint("auth_api", __name__, url_prefix="/api/v1/auth")


def _client_ip() -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr


def _establish_session(user_id: int, tokens: dict) -> None:
    flask_session.permanent = True
    flask_session["user_id"] = user_id
    flask_session["auth_type"] = "session"
    refresh = tokens["refresh_token"]
    flask_session["refresh_token"] = refresh
    UserRepository(db_session()).create_session(
        user_id=user_id, token=refresh, ip=_client_ip(),
        user_agent=request.headers.get("User-Agent"),
        expires_at=utcnow() + timedelta(minutes=settings.refresh_token_expire_minutes),
    )


def _payload_model(schema_class):
    """Validate the JSON body against a Pydantic schema."""
    data = request.get_json(silent=True) or {}
    try:
        return schema_class(**data), data
    except Exception as exc:
        raise ValidationError(_first_validation_error(exc)) from exc


def _first_validation_error(exc: Exception) -> str:
    errors = getattr(exc, "errors", lambda: [])()
    if errors:
        first = errors[0]
        loc = ".".join(str(x) for x in first.get("loc", []))
        return f"{loc}: {first.get('msg', 'invalid value')}" if loc else first.get("msg", "invalid value")
    return str(exc)


@bp.post("/register")
def register():
    payload, _ = _payload_model(RegisterRequest)
    username = strip_dangerous_tags(payload.username).strip()
    user = auth_service.register(
        db_session(), payload.email, username, payload.password, payload.full_name
    )
    tokens = auth_service.token_pair(user.id)
    _establish_session(user.id, tokens)
    return jsonify({**tokens, "user_id": user.id, "username": user.username})


@bp.post("/login")
def login():
    payload, _ = _payload_model(LoginRequest)
    tokens = auth_service.login(
        db_session(), payload.identifier.strip(), payload.password,
        ip=_client_ip(), user_agent=request.headers.get("User-Agent"),
    )
    user = UserRepository(db_session()).get_by_email(payload.identifier) or \
        UserRepository(db_session()).get_by_username(payload.identifier)
    _establish_session(user.id, tokens)
    return jsonify({**tokens, "user_id": user.id, "username": user.username})


@bp.post("/logout")
def logout():
    user_id = flask_session.get("user_id")
    if user_id:
        refresh = flask_session.pop("refresh_token", None)
        if refresh:
            auth_service.logout(db_session(), refresh)
    flask_session.clear()
    return jsonify({"detail": "Logged out"})


@bp.post("/logout-all")
@login_required
def logout_all():
    user = current_user()
    count = auth_service.logout_all(db_session(), user.id)
    flask_session.clear()
    return jsonify({"detail": f"Revoked {count} session(s)"})


@bp.get("/me")
@login_required
def me():
    user = current_user()
    return jsonify({
        "id": user.id, "email": user.email, "username": user.username,
        "full_name": user.full_name, "is_admin": user.is_admin,
        "is_verified": user.is_verified, "role": user.role, "theme": user.theme,
        "high_contrast": user.high_contrast, "created_at": user.created_at.isoformat(),
    })


@bp.post("/change-password")
@login_required
def change_password():
    payload, _ = _payload_model(PasswordChangeRequest)
    auth_service.change_password(db_session(), current_user(),
                                 payload.current_password, payload.new_password)
    return jsonify({"detail": "Password changed"})


@bp.post("/forgot-password")
def forgot_password():
    payload, _ = _payload_model(PasswordResetRequest)
    info = auth_service.reset_request(db_session(), payload.email)
    if info["token"] and info["email_enabled"]:
        link = url_for("pages.reset", token=info["token"], _external=True)
        send_email(payload.email, "AEGIS password reset",
                   f"<p>Use this link to reset your password:</p><p><a href='{link}'>Reset password</a></p>")
    return jsonify({"detail": "If that email exists, a reset link has been sent.",
                    "token": info["token"] if not settings.email_enabled else None})


@bp.post("/reset-password")
def reset_password():
    payload, _ = _payload_model(PasswordResetConfirm)
    auth_service.reset_confirm(db_session(), payload.token, payload.new_password)
    return jsonify({"detail": "Password has been reset. You can now log in."})


@bp.post("/verify-email")
def verify_email():
    payload, _ = _payload_model(VerifyEmailRequest)
    user = auth_service.verify_email(db_session(), payload.token)
    return jsonify({"detail": "Email verified", "user_id": user.id})
