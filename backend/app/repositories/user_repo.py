"""User repository: DB access for user records."""
from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import User, UserSetting, UserSession
from app.security.jwt import hash_opaque
from app.utils.time import utcnow


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    # --- reads --------------------------------------------------------------
    def get(self, user_id: int) -> User | None:
        return self.db.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        return self.db.scalar(select(User).where(func.lower(User.email) == email.lower()))

    def get_by_username(self, username: str) -> User | None:
        return self.db.scalar(select(User).where(func.lower(User.username) == username.lower()))

    def list_users(self, page: int = 1, page_size: int = 20, search: str | None = None):
        stmt = select(User).order_by(User.id.desc())
        if search:
            like = f"%{search}%"
            stmt = stmt.where(
                (User.email.ilike(like)) | (User.username.ilike(like)) | (User.full_name.ilike(like))
            )
        total = len(self.db.scalars(stmt).all())
        items = self.db.scalars(
            stmt.offset((page - 1) * page_size).limit(page_size)
        ).all()
        return total, items

    def count(self) -> int:
        return self.db.scalar(select(func.count(User.id))) or 0

    def active_count(self) -> int:
        return self.db.scalar(select(func.count(User.id)).where(User.is_active.is_(True))) or 0

    def new_users_last_30_days(self) -> int:
        cutoff = utcnow() - timedelta(days=30)
        return (
            self.db.scalar(select(func.count(User.id)).where(User.created_at >= cutoff)) or 0
        )

    # --- writes --------------------------------------------------------------
    def create(self, email: str, username: str, hashed_password: str,
               full_name: str | None = None) -> User:
        user = User(
            email=email, username=username, hashed_password=hashed_password,
            full_name=full_name,
        )
        self.db.add(user)
        self.db.flush()
        self.db.add(UserSetting(user_id=user.id))
        return user

    def save(self, user: User) -> None:
        self.db.add(user)
        self.db.flush()

    def delete(self, user: User) -> None:
        self.db.delete(user)
        self.db.flush()

    # --- sessions -------------------------------------------------------------
    def create_session(self, user_id: int, token: str, ip: str | None,
                       user_agent: str | None, expires_at: datetime) -> UserSession:
        session = UserSession(
            user_id=user_id,
            token_hash=hash_opaque(token),
            ip_address=ip,
            user_agent=(user_agent or "")[:500],
            expires_at=expires_at,
        )
        self.db.add(session)
        self.db.flush()
        return session

    def get_session(self, token: str) -> UserSession | None:
        return self.db.scalar(
            select(UserSession).where(UserSession.token_hash == hash_opaque(token))
        )

    def revoke_session(self, session: UserSession) -> None:
        session.revoked = True
        self.db.add(session)

    def revoke_all_sessions(self, user_id: int, except_session_id: int | None = None) -> int:
        stmt = select(UserSession).where(
            UserSession.user_id == user_id, UserSession.revoked.is_(False)
        )
        if except_session_id:
            stmt = stmt.where(UserSession.id != except_session_id)
        sessions = self.db.scalars(stmt).all()
        for session in sessions:
            session.revoked = True
            self.db.add(session)
        return len(sessions)

    def get_settings(self, user_id: int) -> UserSetting | None:
        return self.db.scalar(select(UserSetting).where(UserSetting.user_id == user_id))
