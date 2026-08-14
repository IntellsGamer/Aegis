"""Notification service: in-app + email + SSE real-time stream.

Server-Sent Events (SSE) are used instead of WebSockets because the
application is served over WSGI (gunicorn).
"""
from __future__ import annotations

import logging
import queue
import smtplib
import threading
from email.message import EmailMessage

from app.config import settings
from app.repositories.notification_repo import NotificationRepository

logger = logging.getLogger("aegis.notify")

# In-memory pub/sub: user_id -> thread-safe queue of payloads.
_subs: dict[int, set[queue.Queue]] = {}
_lock = threading.Lock()


def subscribe(user_id: int) -> queue.Queue:
    q: queue.Queue = queue.Queue(maxsize=100)
    with _lock:
        _subs.setdefault(user_id, set()).add(q)
    return q


def unsubscribe(user_id: int, q: queue.Queue) -> None:
    with _lock:
        _subs.setdefault(user_id, set()).discard(q)


def publish(user_id: int, payload: dict) -> None:
    with _lock:
        targets = list(_subs.get(user_id, ()))
    for q in targets:
        try:
            q.put_nowait(payload)
        except queue.Full:
            pass


def send_email(to: str, subject: str, html: str) -> bool:
    if not settings.email_enabled or not settings.smtp_host:
        return False
    try:
        message = EmailMessage()
        message["From"] = settings.smtp_from
        message["To"] = to
        message["Subject"] = subject
        message.set_content("This message requires an HTML capable client.")
        message.add_alternative(html, subtype="html")
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as smtp:
            smtp.starttls()
            if settings.smtp_user:
                smtp.login(settings.smtp_user, settings.smtp_password or "")
            smtp.send_message(message)
        return True
    except Exception as exc:  # pragma: no cover
        logger.warning("email send failed: %s", exc)
        return False


def create_and_notify(db, user_id: int | None, title: str, body: str | None,
                      kind: str = "info", link: str | None = None,
                      email_to: str | None = None) -> None:
    """Persist an in-app notification and optionally fan out via SSE/email."""
    repo = NotificationRepository(db)
    repo.create(user_id=user_id, title=title, body=body, kind=kind, channel="app", link=link)
    db.commit()

    if user_id and settings.push_enabled:
        publish(user_id, {"type": kind, "title": title, "body": body, "link": link,
                          "ts": __import__("datetime").datetime.utcnow().isoformat()})

    if email_to and settings.email_enabled:
        send_email(email_to, title, f"<p>{body or ''}</p>")
