"""Analytics API blueprint (public aggregate data, no PII)."""
from __future__ import annotations

from datetime import timedelta

from flask import Blueprint, jsonify, request
from sqlalchemy import func, select

from app.dependencies import db_session
from app.models import Scan
from app.repositories.scan_repo import ScanRepository
from app.services import admin_service
from app.utils.time import utcnow

bp = Blueprint("analytics_api", __name__, url_prefix="/api/v1/analytics")


@bp.get("/summary")
def summary():
    """Per-user dashboard summary (requires login)."""
    from app.dependencies import current_user, login_required

    user = current_user()
    if not user:
        return jsonify({"detail": "Authentication required"}), 401
    db = db_session()
    rows = db.scalars(
        select(Scan).where(Scan.user_id == user.id).order_by(Scan.id.desc()).limit(200)
    ).all()
    # Use risk_level instead of verdict
    threats = [r for r in rows if r.risk_level in ("high", "critical")]
    suspicious = [r for r in rows if r.risk_level == "medium"]
    scores = [r.trust_score for r in rows if r.trust_score is not None]
    avg = round(sum(scores) / len(scores), 1) if scores else None
    saved = len(threats)
    # Map risk_level to verdict for display
    def get_verdict(risk_level):
        if risk_level in ("high", "critical"):
            return "threat"
        elif risk_level == "medium":
            return "suspicious"
        else:
            return "safe"
    return jsonify({
        "scans": len(rows),
        "threats": len(threats),
        "avg_score": avg,
        "saved": saved,
        "recent_threats": [{
            "id": r.id, "target": r.input_url or r.input_text or r.file_name or str(r.id),
            "domain": r.input_url or r.input_text or r.file_name or str(r.id), "verdict": get_verdict(r.risk_level),
            "vector": r.scan_type, "created_at": r.created_at.isoformat() if r.created_at else None,
        } for r in (threats + suspicious)[:5]],
    })


@bp.get("/overview")
def overview():
    return jsonify(admin_service.analytic_breakdown(db_session()))


@bp.get("/trends")
def trends():
    days = min(request.args.get("days", 30, type=int), 90)
    scan_repo = ScanRepository(db_session())
    daily = scan_repo.count_by_day(days)
    out = []
    for i in range(days - 1, -1, -1):
        day = (utcnow() - timedelta(days=i)).strftime("%Y-%m-%d")
        out.append({"date": day, "count": daily.get(day, 0)})
    return jsonify(out)


@bp.get("/categories")
def categories():
    db = db_session()
    rows = db.execute(
        select(Scan.scan_type, func.count(Scan.id)).group_by(Scan.scan_type)
    ).all()
    return jsonify([{"type": t, "count": n} for t, n in rows])


@bp.get("/risk")
def risk():
    return jsonify(ScanRepository(db_session()).risk_distribution())


@bp.get("/accuracy")
def accuracy():
    db = db_session()
    confident = db.scalar(
        select(func.count(Scan.id)).where(Scan.confidence >= 0.7, Scan.status == "completed")
    ) or 0
    total = db.scalar(select(func.count(Scan.id)).where(Scan.status == "completed")) or 1
    return jsonify({"completed": total, "high_confidence": confident,
                    "accuracy_score": round(confident / total, 3)})
