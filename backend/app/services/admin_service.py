"""Admin statistics, evidence-engine metadata, and threat moderation helpers."""
from __future__ import annotations

from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models import Scan, ScanOutcome, Threat
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


def triage_queue(db: Session, limit: int = 25) -> dict:
    """Return a bounded human-review queue for persisted high-risk scans.

    The queue is descriptive only: assigning an outcome remains a separate,
    authenticated governance action and never changes the evidence-fusion score.
    """
    limit = max(1, min(int(limit), 100))
    candidates = db.scalars(
        select(Scan)
        .where(Scan.risk_level.in_(("high", "critical")), Scan.status == "completed")
        .options(selectinload(Scan.findings))
        .order_by(Scan.completed_at.desc(), Scan.id.desc())
        .limit(limit * 3)
    ).all()
    # A safety-boundary block prevents acquisition; it is not proof of a
    # malicious destination and must never be offered for analyst confirmation.
    scans = [scan for scan in candidates if not any(item.code == "unsafe_destination" for item in scan.findings)][:limit]
    scan_ids = [scan.id for scan in scans]
    latest_outcome: dict[int, ScanOutcome] = {}
    if scan_ids:
        outcomes = db.scalars(
            select(ScanOutcome)
            .where(ScanOutcome.scan_id.in_(scan_ids))
            .order_by(ScanOutcome.scan_id.asc(), ScanOutcome.created_at.desc(), ScanOutcome.id.desc())
        ).all()
        for outcome in outcomes:
            latest_outcome.setdefault(outcome.scan_id, outcome)

    severity_priority = {"critical": 100, "high": 70}
    items = []
    for scan in scans:
        findings = sorted(scan.findings, key=lambda item: item.impact or 0.0)[:4]
        families: dict[str, int] = {}
        for finding in scan.findings:
            families[finding.category or "analysis"] = families.get(finding.category or "analysis", 0) + 1
        outcome = latest_outcome.get(scan.id)
        assessment_state = "limited" if any(item.code == "destination_unresolved" for item in scan.findings) else "blocked" if any(item.code == "unsafe_destination" for item in scan.findings) else "complete"
        items.append({
            "scan_id": scan.id,
            "target": (scan.input_url or scan.input_text or scan.file_name or "")[:500],
            "scan_type": scan.scan_type,
            "risk_level": scan.risk_level,
            "trust_score": scan.trust_score,
            "confidence": scan.confidence,
            "assessment_state": assessment_state,
            "created_at": scan.created_at.isoformat() if scan.created_at else None,
            "priority": severity_priority.get(scan.risk_level, 0) + round((1 - (scan.trust_score or 100) / 100) * 10),
            "evidence_families": [{"name": key, "count": value} for key, value in sorted(families.items())],
            "strongest_evidence": [{
                "code": item.code, "title": item.title, "severity": item.severity,
                "evidence": item.evidence, "impact": item.impact,
            } for item in findings],
            "review": {
                "state": outcome.verdict if outcome else "awaiting_review",
                "recorded_at": outcome.created_at.isoformat() if outcome and outcome.created_at else None,
                "rationale": outcome.rationale if outcome else None,
            },
        })
    return {
        "items": items, "total": len(items), "limit": limit,
        "purpose": "Human review queue for high-risk persisted assessments. Safety-boundary-only blocks are excluded; an outcome is separate from the engine score.",
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
