"""Flask request-context dependencies and auth helpers.

Sessions are signed cookies (Flask). The `current_user` object is cached on
`g` so repositories and templates share the same instance per request.
"""
from __future__ import annotations

from functools import wraps

from flask import g, redirect, request, url_for
from sqlalchemy.orm import Session

from app.exceptions import ForbiddenError, UnauthorizedError
from app.models import User
from app.repositories.user_repo import UserRepository
from app.security.jwt import decode_token


def db_session() -> Session:
    return g.db


def current_user() -> User | None:
    """Resolve the authenticated user from the Flask session cookie or JWT."""
    user = getattr(g, "current_user", None)
    if user is not None:
        return user
    user_id = None

    session_user_id = _session().get("user_id")
    if session_user_id:
        user_id = session_user_id
    else:
        header = request.headers.get("Authorization", "")
        if header.startswith("Bearer "):
            token = header[7:]
            try:
                payload = decode_token(token, expected_type="access")
                user_id = int(payload.get("sub", 0))
            except Exception:
                return None

    if user_id:
        user = UserRepository(g.db).get(int(user_id))
        if user and user.is_active:
            g.current_user = user
            return user
    return None


def optional_user() -> User | None:
    return current_user()


def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        user = current_user()
        if user is None:
            if request.path.startswith("/api/"):
                raise UnauthorizedError("Authentication required")
            return redirect(url_for("pages.login", next=request.path))
        return view(*args, **kwargs)

    return wrapper


def optional_login(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        current_user()
        return view(*args, **kwargs)

    return wrapper


def admin_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        user = current_user()
        if user is None:
            if request.path.startswith("/api/"):
                raise UnauthorizedError("Authentication required")
            return redirect(url_for("pages.login", next=request.path))
        if not user.is_admin:
            if request.path.startswith("/api/"):
                raise ForbiddenError("Administrator privileges required")
            return redirect(url_for("pages.dashboard"))
        return view(*args, **kwargs)

    return wrapper


def get_db() -> Session:
    return g.db


def _session():
    from flask import session

    return session
