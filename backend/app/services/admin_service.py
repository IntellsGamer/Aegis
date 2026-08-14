"""Admin statistics, evidence-engine metadata, and threat moderation helpers."""
from __future__ import annotations

from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Scan, Threat
from app.repositories.admin_repo import AuditLogRepository, ThreatReportRepository, ThreatRepository
from app.repositories.scan_repo import ScanRepository
from app.repositories.user_repo import UserRepository
from app.trust_engine.engine import ENGINE_VERSION
from app.utils.time import utcnow


def prediction_engine_info() -> dict:
    """Describe the active predictor without implying a measured accuracy."""
    return {
        "name": "AEGIS Evidence Fusion",
        "version": ENGINE_VERSION,
        "training_required": False,
        "llm_used": False,
        "prediction_method": "deterministic evidence fusion with calibrated confidence",
        "evidence_sources": [
            "threat intelligence",
            "email authentication",
            "URL and transport observations",
            "page behavior",
            "content and request semantics",
        ],
    }


def dashboard_stats(db: Session) -> dict:
    users = UserRepository(db)
    scans = ScanRepository(db)
    threats = ThreatRepository(db)
    reports = ThreatReportRepository(db)
    audit = AuditLogRepository(db)

    total_scans = scans.count()
    today_scans = scans.count_today()
    high_risk_recent = scans.high_risk_recent(limit=8)
    recent_scans = db.scalars(select(Scan).order_by(Scan.id.desc()).limit(10)).all()
    daily = scans.count_by_day(14)
    weekly = [
        {
            "date": (utcnow() - timedelta(days=index)).strftime("%Y-%m-%d"),
            "count": daily.get((utcnow() - timedelta(days=index)).strftime("%Y-%m-%d"), 0),
        }
        for index in range(13, -1, -1)
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
        "recent_scans": [
            {
                "id": scan.id,
                "type": scan.scan_type,
                "score": scan.trust_score,
                "risk": scan.risk_level,
                "created_at": scan.created_at.isoformat(),
                "summary": scan.summary,
            }
            for scan in recent_scans
        ],
        "high_risk_recent": [
            {
                "id": scan.id,
                "type": scan.scan_type,
                "score": scan.trust_score,
                "risk": scan.risk_level,
                "created_at": scan.created_at.isoformat(),
            }
            for scan in high_risk_recent
        ],
        # Kept as an API-compatible key for existing dashboard consumers.
        "model_info": prediction_engine_info(),
    }


def threat_stats(db: Session) -> dict:
    threats = ThreatRepository(db)
    rows = db.execute(select(Threat.category, func.count(Threat.id)).group_by(Threat.category)).all()
    return {
        "categories": [{"category": category, "count": count} for category, count in rows],
        "total": threats.count() if hasattr(threats, "count") else 0,
    }


def analytic_breakdown(db: Session) -> dict:
    scans = ScanRepository(db)
    rows = db.execute(select(Scan.scan_type, func.count(Scan.id)).group_by(Scan.scan_type)).all()
    categories = [{"type": scan_type, "count": count} for scan_type, count in rows]
    distribution = scans.risk_distribution()
    completed = scans.count() or 1
    high_confidence = db.scalar(
        select(func.count(Scan.id)).where(Scan.confidence >= 0.7, Scan.status == "completed")
    ) or 0
    return {
        "categories": categories,
        "risk_distribution": distribution,
        "assessment_quality": {
            "completed": completed,
            "high_confidence": high_confidence,
            "high_confidence_share": round(high_confidence / completed, 3),
            "note": "Confidence measures evidence coverage and agreement, not verified accuracy.",
        },
        "totals": {"scans": scans.count(), "today": scans.count_today()},
    }
