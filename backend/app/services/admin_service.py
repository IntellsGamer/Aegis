"""Admin services: stats, model retraining, threat moderation."""
from __future__ import annotations

from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.ai.model_manager import model_manager
from app.models import Scan, Threat, User
from app.repositories.admin_repo import (
    AuditLogRepository,
    ThreatReportRepository,
    ThreatRepository,
)
from app.repositories.scan_repo import ScanRepository
from app.repositories.user_repo import UserRepository
from app.utils.time import utcnow


def dashboard_stats(db: Session) -> dict:
    users = UserRepository(db)
    scans = ScanRepository(db)
    threats = ThreatRepository(db)
    reports = ThreatReportRepository(db)
    audit = AuditLogRepository(db)

    total_scans = scans.count()
    today_scans = scans.count_today()
    high_risk = len([r for r in scans.risk_distribution() if r["risk"] in ("high", "critical")])
    high_risk_recent = scans.high_risk_recent(limit=8)
    recent_scans = db.scalars(
        select(Scan).order_by(Scan.id.desc()).limit(10)
    ).all()

    # weekly trend
    daily = scans.count_by_day(14)
    weekly = [
        {"date": (utcnow() - timedelta(days=i)).strftime("%Y-%m-%d"),
         "count": daily.get((utcnow() - timedelta(days=i)).strftime("%Y-%m-%d"), 0)}
        for i in range(13, -1, -1)
    ]

    return {
        "totals": {
            "users": users.count(),
            "scans": total_scans,
            "scans_today": today_scans,
            "threats": threats.count() if hasattr(threats, "count") else 0,
            "threat_reports": reports.count(),
            "pending_reports": reports.count_pending(),
            "audit_events_7d": audit.count_last_days(7),
            "new_users_30d": users.new_users_last_30_days(),
        },
        "risk_distribution": scans.risk_distribution(),
        "weekly": weekly,
        "recent_scans": [{
            "id": s.id, "type": s.scan_type, "score": s.trust_score,
            "risk": s.risk_level, "created_at": s.created_at.isoformat(),
            "summary": s.summary,
        } for s in recent_scans],
        "high_risk_recent": [{
            "id": s.id, "type": s.scan_type, "score": s.trust_score,
            "risk": s.risk_level, "created_at": s.created_at.isoformat(),
        } for s in high_risk_recent],
        "model_info": model_manager.capabilities(),
    }


def retrain_models(db: Session, extra_text_pairs: list | None = None,
                   extra_url_rows: list | None = None) -> dict:
    """Retrain the ML models using built-in data + optionally user feedback."""
    metrics = model_manager.train_all(extra_text_pairs, extra_url_rows)
    return metrics


def threat_stats(db: Session) -> dict:
    threats = ThreatRepository(db)
    # category breakdown
    rows = db.execute(
        select(Threat.category, func.count(Threat.id)).group_by(Threat.category)
    ).all()
    return {
        "categories": [{"category": c, "count": n} for c, n in rows],
        "total": threats.count() if hasattr(threats, "count") else 0,
    }


def analytic_breakdown(db: Session) -> dict:
    scans = ScanRepository(db)
    rows = db.execute(
        select(Scan.scan_type, func.count(Scan.id)).group_by(Scan.scan_type)
    ).all()
    categories = [{"type": t, "count": n} for t, n in rows]
    distribution = scans.risk_distribution()

    # Detection accuracy proxy: share of scans classified with high confidence
    # matching expected risk (confidence >= 0.7).
    confident = db.scalar(
        select(func.count(Scan.id)).where(Scan.confidence >= 0.7, Scan.status == "completed")
    ) or 0
    completed = scans.count() or 1
    return {
        "categories": categories,
        "risk_distribution": distribution,
        "accuracy": {
            "completed": completed,
            "high_confidence": confident,
            "accuracy_score": round(confident / completed, 3),
        },
        "totals": {"scans": scans.count(), "today": scans.count_today()},
    }
