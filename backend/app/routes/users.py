"""User profile API blueprint."""
from __future__ import annotations

from flask import Blueprint, jsonify, request

from app.dependencies import db_session, login_required
from app.schemas.user import UserSettingsUpdate, UserUpdate
from app.services import user_service

bp = Blueprint("users_api", __name__, url_prefix="/api/v1/users")


def _payload(schema_class, exclude_none: bool = True):
    data = request.get_json(silent=True) or {}
    try:
        payload = schema_class(**data)
    except Exception as exc:
        from app.exceptions import ValidationError

        raise ValidationError(str(exc))
    return payload.model_dump(exclude_none=exclude_none)


def _user_dict(user) -> dict:
    return {
        "id": user.id, "email": user.email, "username": user.username,
        "full_name": user.full_name, "is_admin": user.is_admin,
        "is_verified": user.is_verified, "role": user.role, "theme": user.theme,
        "high_contrast": user.high_contrast, "locale": user.locale,
        "avatar": user.avatar, "created_at": user.created_at.isoformat() if user.created_at else None,
        "last_login": user.last_login.isoformat() if user.last_login else None,
    }


def _settings_dict(row) -> dict | None:
    if row is None:
        return None
    return {
        "notify_email": row.notify_email, "notify_push": row.notify_push,
        "notify_threats": row.notify_threats, "save_history": row.save_history,
        "anonymous_reports": row.anonymous_reports, "language": row.language,
    }


@bp.get("/me")
@login_required
def me():
    from app.dependencies import current_user

    return jsonify(_user_dict(current_user()))


@bp.patch("/me")
@login_required
def update_me():
    from app.dependencies import current_user

    data = _payload(UserUpdate)
    user = user_service.update_profile(db_session(), current_user(), data)
    return jsonify(_user_dict(user))


@bp.get("/me/settings")
@login_required
def get_settings():
    from app.dependencies import current_user

    return jsonify(_settings_dict(current_user().settings))


@bp.patch("/me/settings")
@login_required
def update_settings():
    from app.dependencies import current_user

    data = _payload(UserSettingsUpdate)
    user_service.update_settings(db_session(), current_user(), data)
    return jsonify(_settings_dict(current_user().settings))


@bp.get("/search")
def search_users():
    q = request.args.get("q", "")
    items = user_service.search_users(db_session(), q, limit=8)
    return jsonify([_user_dict(u) for u in items])


@bp.delete("/me")
@login_required
def delete_me():
    from app.dependencies import current_user

    user_service.delete_account(db_session(), current_user())
    return jsonify({"detail": "Account deleted"})
