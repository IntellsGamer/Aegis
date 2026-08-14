"""Global search API: scan history + threat database."""
from __future__ import annotations

from flask import Blueprint, jsonify, request
from sqlalchemy import or_, select

from app.dependencies import db_session, login_required
from app.models import Scan, Threat

bp = Blueprint("search_api", __name__, url_prefix="/api/v1/search")


@bp.get("")
@login_required
def search():
    q = request.args.get("q", "")
    if len(q) < 1:
        return jsonify({"query": q, "scans": [], "threats": []})
    like = f"%{q}%"
    db = db_session()
    from app.dependencies import current_user

    user = current_user()
    scans = db.scalars(
        select(Scan)
        .where(Scan.user_id == user.id)
        .where(or_(
            Scan.input_text.ilike(like), Scan.input_url.ilike(like),
            Scan.file_name.ilike(like), Scan.summary.ilike(like),
        ))
        .order_by(Scan.id.desc()).limit(20)
    ).all()
    threats = db.scalars(
        select(Threat)
        .where(Threat.active.is_(True))
        .where(or_(Threat.value.ilike(like), Threat.category.ilike(like)))
        .order_by(Threat.hits.desc()).limit(20)
    ).all()
    return jsonify({
        "query": q,
        "scans": [{
            "id": s.id, "type": s.scan_type, "score": s.trust_score,
            "risk": s.risk_level, "summary": s.summary,
            "created_at": s.created_at.isoformat() if s.created_at else None,
            "preview": (s.input_url or s.input_text or s.file_name or "")[:200],
        } for s in scans],
        "threats": [{
            "id": t.id, "type": t.threat_type, "value": t.value,
            "category": t.category, "severity": t.severity, "hits": t.hits,
        } for t in threats],
    })
