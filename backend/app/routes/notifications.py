"""Notification API + Server-Sent Events real-time stream.

SSE works over WSGI (gunicorn) where WebSockets are not possible.
"""
from __future__ import annotations

import json
import queue
import time

from flask import Blueprint, Response, jsonify, request

from app.dependencies import db_session, login_required
from app.exceptions import NotFoundError
from app.repositories.notification_repo import NotificationRepository
from app.services import notification_service

bp = Blueprint("notifications_api", __name__, url_prefix="/api/v1/notifications")


@bp.get("")
@login_required
def list_notifications():
    from app.dependencies import current_user

    repo = NotificationRepository(db_session())
    items = repo.list_for_user(current_user().id, 50)
    return jsonify({
        "unread": repo.unread_count(current_user().id),
        "items": [
            {"id": n.id, "kind": n.kind, "title": n.title, "body": n.body,
             "link": n.link, "is_read": n.is_read,
             "created_at": n.created_at.isoformat() if n.created_at else None}
            for n in items
        ],
    })


@bp.post("/<int:notification_id>/read")
@login_required
def mark_read(notification_id: int):
    from app.dependencies import current_user

    repo = NotificationRepository(db_session())
    items = repo.list_for_user(current_user().id, 500)
    notification = next((n for n in items if n.id == notification_id), None)
    if not notification:
        raise NotFoundError("Notification not found")
    repo.mark_read(notification)
    return jsonify({"detail": "Marked read"})


@bp.post("/read-all")
@login_required
def mark_all_read():
    from app.dependencies import current_user

    repo = NotificationRepository(db_session())
    count = repo.mark_all_read(current_user().id)
    return jsonify({"detail": f"Marked {count} notifications read"})


@bp.get("/stream")
@login_required
def stream():
    """Server-Sent Events endpoint for real-time notifications."""
    from app.dependencies import current_user

    user = current_user()

    def generate():
        q = notification_service.subscribe(user.id)
        # send a heartbeat / initial event
        yield "event: connected\ndata: {}\n\n"
        try:
            while True:
                try:
                    payload = q.get(timeout=15)
                    yield f"event: message\ndata: {json.dumps(payload)}\n\n"
                except queue.Empty:
                    yield ": keepalive\n\n"
        finally:
            notification_service.unsubscribe(user.id, q)

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
