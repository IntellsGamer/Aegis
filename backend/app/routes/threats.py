"""Threat API blueprint: search, community reports, anonymous map."""
from __future__ import annotations

from flask import Blueprint, jsonify, request

from app.dependencies import db_session, optional_login
from app.exceptions import ValidationError
from app.repositories.admin_repo import ThreatReportRepository, ThreatRepository

bp = Blueprint("threats_api", __name__, url_prefix="/api/v1/threats")


@bp.get("/search")
def search_threats():
    q = request.args.get("q", "")
    if len(q) < 2:
        return jsonify([])
    repo = ThreatRepository(db_session())
    results = repo.search(q, limit=20)
    return jsonify([
        {"id": t.id, "type": t.threat_type, "value": t.value, "category": t.category,
         "severity": t.severity, "hits": t.hits,
         "last_seen": t.last_seen.isoformat() if t.last_seen else None}
        for t in results
    ])


@bp.post("/report")
@optional_login
def submit_report():
    data = request.get_json(silent=True) or {}
    content_type = data.get("content_type", "url")
    content = (data.get("content") or "").strip()
    if not content:
        raise ValidationError("Content is required")
    from app.dependencies import current_user

    payload = {
        "content_type": content_type,
        "content": content[:500],
        "category": data.get("category", "unknown"),
        "description": (data.get("description") or "")[:1000],
        "latitude": data.get("latitude"),
        "longitude": data.get("longitude"),
        "country": data.get("country"),
        "country_name": data.get("country_name"),
    }
    user = current_user()
    if user:
        payload["user_id"] = user.id
    repo = ThreatReportRepository(db_session())
    report = repo.create(payload)
    return jsonify({
        "id": report.id, "content_type": report.content_type, "content": report.content,
        "category": report.category, "status": report.status, "votes": report.votes,
        "created_at": report.created_at.isoformat() if report.created_at else None,
    })


@bp.get("/map")
def threat_map():
    repo = ThreatReportRepository(db_session())
    points = repo.geo_points()
    countries = repo.country_counts()
    return jsonify({
        "points": [{"lat": p["lat"], "lng": p["lng"], "risk": p["category"] or "unknown",
                    "type": p["type"], "country": p["country"]} for p in points],
        "countries": countries,
        "total_reports": repo.count(),
    })
