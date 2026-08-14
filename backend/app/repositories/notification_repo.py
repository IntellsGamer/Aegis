"""Notification repository."""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Notification
from app.utils.time import utcnow


class NotificationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, user_id: int | None, title: str, body: str | None = None,
               kind: str = "info", channel: str = "app", link: str | None = None,
               data: str | None = None) -> Notification:
        notification = Notification(
            user_id=user_id, title=title, body=body, kind=kind,
            channel=channel, link=link, data=data,
        )
        self.db.add(notification)
        self.db.flush()
        return notification

    def list_for_user(self, user_id: int, limit: int = 50, unread_only: bool = False):
        stmt = (
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.id.desc())
            .limit(limit)
        )
        if unread_only:
            stmt = stmt.where(Notification.is_read.is_(False))
        return self.db.scalars(stmt).all()

    def unread_count(self, user_id: int) -> int:
        return (
            self.db.scalar(
                select(func.count(Notification.id)).where(
                    Notification.user_id == user_id, Notification.is_read.is_(False)
                )
            ) or 0
        )

    def mark_read(self, notification: Notification) -> None:
        notification.is_read = True
        self.db.add(notification)

    def mark_all_read(self, user_id: int) -> int:
        items = self.db.scalars(
            select(Notification).where(Notification.user_id == user_id, Notification.is_read.is_(False))
        ).all()
        for item in items:
            item.is_read = True
            self.db.add(item)
        return len(items)
