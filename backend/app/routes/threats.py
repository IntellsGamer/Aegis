"""Threat API blueprint: search, community reports, anonymous map."""
from __future__ import annotations

from flask import Blueprint, jsonify, request

from app.config import settings

from app.dependencies import db_session, optional_login
from app.exceptions import ValidationError
from app.repositories.admin_repo import ThreatReportRepository, ThreatRepository
from app.services import geo_service

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

    # Public map coordinates are never accepted from an untrusted client. A
    # report remains pending until moderation; approved reports are displayed
    # only as country-level aggregates.
    # URL reports must map to the reported destination, never the submitter or
    # arbitrary client-supplied geography. Non-URL reports keep the existing
    # optional country field for explicit, independently verified submissions.
    destination_origin = geo_service.website_origin(content) if content_type == "url" else {}
    country = (
        destination_origin.get("country")
        if content_type == "url" else (data.get("country") or "").strip().upper()
    )
    payload = {
        "content_type": content_type,
        "content": content[:500],
        "category": data.get("category", "unknown"),
        "description": (data.get("description") or "")[:1000],
        "country": country[:4] or None,
        "country_name": (
            destination_origin.get("country_name")
            if content_type == "url" else (data.get("country_name") or "").strip()[:128]
        ) or None,
        "latitude": None,
        "longitude": None,
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
    try:
        range_days = int(request.args.get("range", "1"))
    except ValueError:
        raise ValidationError("Map range must be an integer number of days")
    if range_days not in {1, 7, 30}:
        raise ValidationError("Map range must be one of: 1, 7, or 30 days")

    repo = ThreatReportRepository(db_session())
    points = repo.map_aggregates(range_days)
    countries = repo.country_counts(range_days)
    total_reports = repo.approved_count(range_days)
    return jsonify({
        "points": points,
        "countries": countries,
        "total_reports": total_reports,
        "range_days": range_days,
        "data_state": (
            "development_demo_reports"
            if settings.environment == "development" else "verified_approved_reports"
        ),
        "location_precision": "country_aggregate",
        "development_demo_country": (
            settings.development_report_country
            if settings.environment == "development" else None
        ),
        "empty_reason": (
            "No approved reports with a verified country are available for this period."
            if not points else None
        ),
    })
