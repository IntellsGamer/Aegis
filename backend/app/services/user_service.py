"""User profile and settings services."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import User
from app.repositories.notification_repo import NotificationRepository
from app.repositories.user_repo import UserRepository


def get_profile(db: Session, user: User) -> dict:
    notifications = NotificationRepository(db)
    return {
        "user": user,
        "settings": user.settings,
        "unread_notifications": notifications.unread_count(user.id),
    }


def update_profile(db: Session, user: User, data: dict) -> User:
    users = UserRepository(db)
    for key in ("full_name", "locale", "theme", "high_contrast", "avatar"):
        value = data.get(key)
        if value is not None and hasattr(user, key):
            setattr(user, key, value)

    # ``User.locale`` is the rendering authority for html lang/dir. Keep the
    # legacy settings language in sync for API consumers that still read it.
    if data.get("locale") is not None:
        settings_row = user.settings
        if settings_row is None:
            from app.models import UserSetting

            settings_row = UserSetting(user_id=user.id)
            db.add(settings_row)
        settings_row.language = user.locale
        db.add(settings_row)
    users.save(user)
    return user


def update_settings(db: Session, user: User, data: dict) -> User:
    settings_row = user.settings
    if settings_row is None:
        from app.models import UserSetting

        settings_row = UserSetting(user_id=user.id)
        db.add(settings_row)
    for key in ("notify_email", "notify_push", "notify_threats", "save_history",
                "anonymous_reports", "language"):
        value = data.get(key)
        if value is not None and hasattr(settings_row, key):
            setattr(settings_row, key, value)
    if data.get("language") is not None:
        user.locale = settings_row.language
        db.add(user)
    db.add(settings_row)
    db.flush()
    return user


def delete_account(db: Session, user: User) -> None:
    UserRepository(db).delete(user)


def search_users(db: Session, query: str, limit: int = 8) -> list[User]:
    from sqlalchemy import or_

    like = f"%{query}%"
    return db.query(User).filter(
        or_(User.username.ilike(like), User.email.ilike(like), User.full_name.ilike(like))
    ).limit(limit).all()
