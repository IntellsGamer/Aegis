"""Background tasks: model training, digests, housekeeping."""
from __future__ import annotations

import logging

logger = logging.getLogger("aegis.workers")


def _with_app(func):
    """Wrap a task so it runs inside the Flask application context."""

    def wrapper(*args, **kwargs):
        from app.workers.celery_app import create_flask_app

        app = create_flask_app()
        with app.app_context():
            return func(*args, **kwargs)

    return wrapper


@_with_app
def train_models_task() -> dict:
    from app.ai.model_manager import model_manager

    logger.info("Starting model retraining task")
    metrics = model_manager.train_all()
    logger.info("Model retraining complete: %s", metrics)
    return metrics


@_with_app
def send_weekly_digest_task() -> int:
    """Aggregate weekly stats and email them to admins (if email enabled)."""
    from app.config import settings
    from app.database import SessionLocal
    from app.repositories.user_repo import UserRepository
    from app.services.admin_service import dashboard_stats
    from app.services.notification_service import send_email

    if not settings.email_enabled:
        return 0
    db = SessionLocal()
    try:
        stats = dashboard_stats(db)
        users = UserRepository(db)
        admins = users.list_users(page=1, page_size=100)[1]
        sent = 0
        for admin in admins:
            if not admin.is_admin or not admin.email:
                continue
            body = (
                f"<h3>AEGIS Weekly Digest</h3>"
                f"<p>Scans: {stats['totals']['scans']} (today {stats['totals']['scans_today']})</p>"
                f"<p>New users (30d): {stats['totals']['new_users_30d']}</p>"
                f"<p>Threat reports: {stats['totals']['threat_reports']}</p>"
            )
            if send_email(admin.email, "AEGIS Weekly Security Digest", body):
                sent += 1
        return sent
    finally:
        db.close()


@_with_app
def cleanup_uploads_task(days: int = 30) -> int:
    """Delete uploaded scan files older than `days`."""
    import os
    from pathlib import Path

    from app.config import settings

    removed = 0
    root = Path(settings.upload_dir)
    if not root.exists():
        return 0
    for path in root.rglob("*"):
        if path.is_file():
            try:
                age = (__import__("time").time() - path.stat().st_mtime) / 86400
                if age > days:
                    path.unlink()
                    removed += 1
            except OSError:
                continue
    return removed
