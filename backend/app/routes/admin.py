"""Admin API blueprint: users, threats, keywords, rules, logs, retraining."""
from __future__ import annotations

import re

from flask import Blueprint, jsonify, request

from app.dependencies import admin_required, current_user, db_session
from app.exceptions import NotFoundError, ValidationError
from app.repositories.admin_repo import (
    AuditLogRepository,
    KeywordRepository,
    RuleRepository,
    ThreatReportRepository,
    ThreatRepository,
)
from app.repositories.scan_repo import ScanRepository
from app.repositories.user_repo import UserRepository
from app.services import admin_service

bp = Blueprint("admin_api", __name__, url_prefix="/api/v1/admin")


# --------------------------------------------------------------------------
# Stats
# --------------------------------------------------------------------------
@bp.get("/stats")
@admin_required
def stats():
    return jsonify(admin_service.dashboard_stats(db_session()))


@bp.get("/analytics")
@admin_required
def analytics():
    return jsonify(admin_service.analytic_breakdown(db_session()))


@bp.get("/readiness")
@admin_required
def readiness():
    """Expose operational trust controls without relabelling confidence as accuracy."""
    from app.repositories.governance_repo import GovernanceRepository

    db = db_session()
    feeds = GovernanceRepository(db).list_feeds()
    feed_rows = [{
        "slug": feed.slug, "provider": feed.provider, "enabled": feed.enabled,
        "terms_accepted": feed.terms_accepted, "last_status": feed.last_status,
        "last_success_at": feed.last_success_at.isoformat() if feed.last_success_at else None,
        "data_boundary": (feed.metadata_json or {}).get("data_boundary"),
    } for feed in feeds]
    return jsonify({
        "engine": admin_service.prediction_engine_info(),
        "assessment_quality": admin_service.analytic_breakdown(db).get("assessment_quality", {}),
        "outcome_review": GovernanceRepository(db).outcome_summary(30),
        "feeds": feed_rows,
        "safeguards": [
            {"control": "No training boundary", "detail": "Scan outcomes and feedback are retained for review; they do not automatically retrain a model or rewrite rule weights."},
            {"control": "Acquisition boundary", "detail": "Private, reserved, loopback, and non-web destinations are blocked before remote acquisition."},
            {"control": "Retention consent", "detail": "Private results are retained only when the user explicitly opts into scan history."},
            {"control": "Public intelligence governance", "detail": "Only approved community reports appear on public country-level activity views."},
        ],
        "measurement_note": "Coverage confidence is not a claim of measured accuracy. Confirmed outcomes remain separately governed review data.",
    })


# --------------------------------------------------------------------------
# Users
# --------------------------------------------------------------------------
@bp.get("/users")
@admin_required
def list_users():
    page = request.args.get("page", 1, type=int)
    page_size = min(request.args.get("page_size", 20, type=int), 100)
    search = request.args.get("search")
    repo = UserRepository(db_session())
    total, items = repo.list_users(page, page_size, search)
    return jsonify({
        "total": total, "page": page, "page_size": page_size,
        "items": [{
            "id": u.id, "email": u.email, "username": u.username,
            "full_name": u.full_name, "is_active": u.is_active,
            "is_admin": u.is_admin, "role": u.role, "is_verified": u.is_verified,
            "created_at": u.created_at.isoformat() if u.created_at else None,
            "last_login": u.last_login.isoformat() if u.last_login else None,
        } for u in items],
    })


@bp.patch("/users/<int:user_id>")
@admin_required
def update_user(user_id: int):
    from app.models import User

    repo = UserRepository(db_session())
    user = repo.get(user_id)
    if not user:
        raise NotFoundError("User not found")
    data = request.get_json(silent=True) or {}
    allowed = {"is_active", "is_admin", "role", "is_verified"}
    for key, value in data.items():
        if key in allowed and value is not None:
            setattr(user, key, bool(value) if key != "role" else str(value))
    repo.save(user)
    return jsonify({"detail": "User updated"})


@bp.delete("/users/<int:user_id>")
@admin_required
def delete_user(user_id: int):
    repo = UserRepository(db_session())
    user = repo.get(user_id)
    if not user:
        raise NotFoundError("User not found")
    repo.delete(user)
    return jsonify({"detail": "User deleted"})


# --------------------------------------------------------------------------
# Threats
# --------------------------------------------------------------------------
@bp.get("/threats")
@admin_required
def list_threats():
    page = request.args.get("page", 1, type=int)
    page_size = min(request.args.get("page_size", 50, type=int), 200)
    category = request.args.get("category")
    repo = ThreatRepository(db_session())
    total, items = repo.list(page, page_size, category)
    return jsonify({
        "total": total, "page": page, "page_size": page_size,
        "items": [_threat_dict(t) for t in items],
    })


@bp.post("/threats")
@admin_required
def create_threat():
    data = request.get_json(silent=True) or {}
    value = (data.get("value") or "").strip()
    if not value:
        raise ValidationError("value is required")
    threat = ThreatRepository(db_session()).create({
        "threat_type": data.get("threat_type", "url"),
        "value": value,
        "category": data.get("category", "phishing"),
        "title": data.get("title"),
        "description": data.get("description"),
        "confidence": float(data.get("confidence", 0.9)),
        "severity": data.get("severity", "high"),
        "source": data.get("source", "manual"),
    })
    return jsonify(_threat_dict(threat)), 201


@bp.patch("/threats/<int:threat_id>")
@admin_required
def update_threat(threat_id: int):
    repo = ThreatRepository(db_session())
    threat = repo.get(threat_id)
    if not threat:
        raise NotFoundError("Threat not found")
    data = request.get_json(silent=True) or {}
    repo.update(threat, data)
    return jsonify(_threat_dict(threat))


@bp.delete("/threats/<int:threat_id>")
@admin_required
def delete_threat(threat_id: int):
    repo = ThreatRepository(db_session())
    threat = repo.get(threat_id)
    if not threat:
        raise NotFoundError("Threat not found")
    repo.delete(threat)
    return jsonify({"detail": "Threat deleted"})


def _threat_dict(t) -> dict:
    return {
        "id": t.id, "threat_type": t.threat_type, "value": t.value,
        "category": t.category, "title": t.title, "description": t.description,
        "confidence": t.confidence, "severity": t.severity,
        "source": t.source, "active": t.active, "hits": t.hits,
        "first_seen": t.first_seen.isoformat() if t.first_seen else None,
        "last_seen": t.last_seen.isoformat() if t.last_seen else None,
    }


# --------------------------------------------------------------------------
# Threat reports (community)
# --------------------------------------------------------------------------
@bp.get("/reports")
@admin_required
def list_reports():
    page = request.args.get("page", 1, type=int)
    page_size = min(request.args.get("page_size", 50, type=int), 200)
    status = request.args.get("status")
    repo = ThreatReportRepository(db_session())
    total, items = repo.list(status, page, page_size)
    return jsonify({
        "total": total, "page": page, "page_size": page_size,
        "items": [{
            "id": r.id, "content_type": r.content_type, "content": r.content,
            "category": r.category, "status": r.status, "votes": r.votes,
            "country": r.country, "country_name": r.country_name,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        } for r in items],
    })


@bp.post("/reports/<int:report_id>/approve")
@admin_required
def approve_report(report_id: int):
    repo = ThreatReportRepository(db_session())
    report = repo.get(report_id)
    if not report:
        raise NotFoundError("Report not found")
    repo.update_status(report, "approved")
    # promote to threat database
    ThreatRepository(db_session()).create({
        "threat_type": report.content_type,
        "value": report.content[:512],
        "category": report.category,
        "description": report.description,
        "source": "community",
    })
    return jsonify({"detail": "Report approved and added to threat database"})


@bp.post("/reports/<int:report_id>/reject")
@admin_required
def reject_report(report_id: int):
    repo = ThreatReportRepository(db_session())
    report = repo.get(report_id)
    if not report:
        raise NotFoundError("Report not found")
    repo.update_status(report, "rejected")
    return jsonify({"detail": "Report rejected"})


# --------------------------------------------------------------------------
# Intelligence feeds and measured outcomes
# --------------------------------------------------------------------------
def _feed_dict(feed) -> dict:
    meta = feed.metadata_json or {}
    return {
        "slug": feed.slug, "provider": feed.provider, "enabled": feed.enabled,
        "terms_accepted": feed.terms_accepted,
        "refresh_interval_minutes": feed.refresh_interval_minutes,
        "last_refreshed_at": feed.last_refreshed_at.isoformat() if feed.last_refreshed_at else None,
        "last_success_at": feed.last_success_at.isoformat() if feed.last_success_at else None,
        "last_status": feed.last_status, "last_error": feed.last_error,
        "terms_url": meta.get("terms_url"), "description": meta.get("description"),
        "automatic_sync": bool(meta.get("automatic_sync", False)),
        "data_boundary": meta.get("data_boundary"),
    }


@bp.get("/feeds")
@admin_required
def list_feeds():
    from app.repositories.governance_repo import GovernanceRepository

    return jsonify([_feed_dict(feed) for feed in GovernanceRepository(db_session()).list_feeds()])


@bp.patch("/feeds/<slug>")
@admin_required
def configure_feed(slug: str):
    from app.repositories.governance_repo import GovernanceRepository

    data = request.get_json(silent=True) or {}
    repo = GovernanceRepository(db_session())
    feed = repo.get_feed(slug)
    if not feed:
        raise NotFoundError("Threat-intelligence source not found")
    try:
        repo.configure_feed(
            feed,
            enabled=bool(data.get("enabled", feed.enabled)),
            terms_accepted=bool(data.get("terms_accepted", feed.terms_accepted)),
            refresh_interval_minutes=data.get("refresh_interval_minutes", feed.refresh_interval_minutes),
        )
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc
    AuditLogRepository(db_session()).add(current_user().id, "feed.configured", "intelligence", meta={"feed": slug, "enabled": feed.enabled})
    return jsonify(_feed_dict(feed))


@bp.post("/feeds/<slug>/indicators")
@admin_required
def import_feed_indicators(slug: str):
    from app.repositories.governance_repo import GovernanceRepository

    data = request.get_json(silent=True) or {}
    indicators = data.get("indicators")
    if not isinstance(indicators, list) or not indicators:
        raise ValidationError("indicators must be a non-empty list")
    if len(indicators) > 5_000:
        raise ValidationError("A single import is limited to 5,000 indicators")
    repo = GovernanceRepository(db_session())
    feed = repo.get_feed(slug)
    if not feed:
        raise NotFoundError("Threat-intelligence source not found")
    try:
        result = repo.import_indicators(feed, indicators)
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc
    AuditLogRepository(db_session()).add(current_user().id, "feed.imported", "intelligence", meta=result)
    return jsonify(result), 201


@bp.get("/outcomes")
@admin_required
def outcome_summary():
    from app.repositories.governance_repo import GovernanceRepository

    days = min(max(request.args.get("days", 30, type=int), 1), 365)
    return jsonify(GovernanceRepository(db_session()).outcome_summary(days))


@bp.post("/scans/<int:scan_id>/outcome")
@admin_required
def record_scan_outcome(scan_id: int):
    from app.models import Scan
    from app.repositories.governance_repo import GovernanceRepository

    scan = db_session().get(Scan, scan_id)
    if not scan:
        raise NotFoundError("Scan not found")
    data = request.get_json(silent=True) or {}
    reasons = [{"code": finding.code, "severity": finding.severity, "impact": finding.impact} for finding in scan.findings]
    try:
        outcome = GovernanceRepository(db_session()).record_outcome(
            scan=scan,
            reviewer_user_id=current_user().id,
            verdict=str(data.get("verdict") or ""),
            rationale=data.get("rationale"),
            engine_version="evidence-fusion-v2",
            evidence_snapshot={
                "trust_score": scan.trust_score, "risk_level": scan.risk_level,
                "confidence": scan.confidence, "findings": reasons,
            },
        )
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc
    AuditLogRepository(db_session()).add(current_user().id, "scan.outcome_recorded", "quality", meta={"scan_id": scan.id, "verdict": outcome.verdict})
    return jsonify({
        "id": outcome.id, "scan_id": outcome.scan_id, "verdict": outcome.verdict,
        "engine_version": outcome.engine_version,
        "created_at": outcome.created_at.isoformat() if outcome.created_at else None,
    }), 201


# --------------------------------------------------------------------------
# Keywords
# --------------------------------------------------------------------------
@bp.get("/keywords")
@admin_required
def list_keywords():
    page = request.args.get("page", 1, type=int)
    page_size = min(request.args.get("page_size", 200, type=int), 500)
    category = request.args.get("category")
    repo = KeywordRepository(db_session())
    total, items = repo.list(page, page_size, category)
    return jsonify({
        "total": total, "page": page, "page_size": page_size,
        "items": [{
            "id": k.id, "keyword": k.keyword, "category": k.category,
            "impact": k.impact, "severity": k.severity, "description": k.description,
            "case_sensitive": k.case_sensitive, "is_regex": k.is_regex, "enabled": k.enabled,
        } for k in items],
    })


@bp.post("/keywords")
@admin_required
def create_keyword():
    data = request.get_json(silent=True) or {}
    keyword = (data.get("keyword") or "").strip()
    if not keyword:
        raise ValidationError("keyword is required")
    repo = KeywordRepository(db_session())
    item = repo.create({
        "keyword": keyword,
        "category": data.get("category", "generic"),
        "impact": float(data.get("impact", -5)),
        "severity": data.get("severity", "medium"),
        "description": data.get("description"),
        "case_sensitive": bool(data.get("case_sensitive", False)),
        "is_regex": bool(data.get("is_regex", False)),
    })
    return jsonify({"id": item.id, "keyword": item.keyword, "detail": "Keyword added"}), 201


@bp.patch("/keywords/<int:keyword_id>")
@admin_required
def update_keyword(keyword_id: int):
    repo = KeywordRepository(db_session())
    item = repo.get(keyword_id)
    if not item:
        raise NotFoundError("Keyword not found")
    data = request.get_json(silent=True) or {}
    repo.update(item, data)
    return jsonify({"detail": "Keyword updated"})


@bp.delete("/keywords/<int:keyword_id>")
@admin_required
def delete_keyword(keyword_id: int):
    repo = KeywordRepository(db_session())
    item = repo.get(keyword_id)
    if not item:
        raise NotFoundError("Keyword not found")
    repo.delete(item)
    return jsonify({"detail": "Keyword deleted"})


# --------------------------------------------------------------------------
# Trust rules
# --------------------------------------------------------------------------
@bp.get("/rules")
@admin_required
def list_rules():
    repo = RuleRepository(db_session())
    enabled = request.args.get("enabled")
    items = repo.list(enabled=bool(enabled) if enabled is not None else None)
    return jsonify([{
        "id": r.id, "code": r.code, "name": r.name, "description": r.description,
        "category": r.category, "impact": r.impact, "weight": r.weight,
        "severity": r.severity, "enabled": r.enabled, "explain": r.explain,
    } for r in items])


@bp.patch("/rules/<int:rule_id>")
@admin_required
def update_rule(rule_id: int):
    repo = RuleRepository(db_session())
    rule = repo.get(rule_id)
    if not rule:
        raise NotFoundError("Rule not found")
    data = request.get_json(silent=True) or {}
    repo.update(rule, data)
    return jsonify({"detail": "Rule updated"})


@bp.put("/rules")
@admin_required
def update_rules_bulk():
    """Bulk update rule weights / activation (used by the admin UI)."""
    data = request.get_json(silent=True) or {}
    updates = data.get("rules") or []
    if not isinstance(updates, list):
        raise ValidationError("rules must be a list")
    repo = RuleRepository(db_session())
    count = 0
    for item in updates:
        rule = repo.get(item.get("id"))
        if not rule:
            continue
        if "weight" in item and item["weight"] is not None:
            rule.weight = float(item["weight"])
        if "is_active" in item and item["is_active"] is not None:
            rule.enabled = bool(item["is_active"])
        repo.update(rule, {})
        count += 1
    return jsonify({"detail": f"Updated {count} rule(s)"})


# --------------------------------------------------------------------------
# Logs
# --------------------------------------------------------------------------
@bp.get("/logs")
@admin_required
def list_logs():
    page = request.args.get("page", 1, type=int)
    page_size = min(request.args.get("page_size", 100, type=int), 500)
    category = request.args.get("category")
    repo = AuditLogRepository(db_session())
    total, items = repo.list(page, page_size, category)
    return jsonify({
        "total": total, "page": page, "page_size": page_size,
        "items": [{
            "id": l.id, "user_id": l.user_id, "action": l.action,
            "category": l.category, "detail": l.detail, "meta": l.meta,
            "ip_address": l.ip_address,
            "created_at": l.created_at.isoformat() if l.created_at else None,
        } for l in items],
    })


# --------------------------------------------------------------------------
# Evidence engine status
# --------------------------------------------------------------------------
@bp.post("/models/retrain")
@admin_required
def retrain():
    return jsonify({
        "status": "disabled",
        "message": "AEGIS Evidence Fusion does not train or use a statistical model.",
    }), 410


@bp.get("/models/info")
@admin_required
def model_info():
    # Route name retained for existing dashboard clients.
    return jsonify(admin_service.prediction_engine_info())


@bp.get("/scans")
@admin_required
def list_all_scans():
    page = request.args.get("page", 1, type=int)
    page_size = min(request.args.get("page_size", 50, type=int), 200)
    scan_repo = ScanRepository(db_session())
    total, items = scan_repo.list_for_user(None, 1, 1)  # not used
    # fetch directly
    from app.models import Scan
    from sqlalchemy import select

    db = db_session()
    stmt = select(Scan).order_by(Scan.id.desc())
    all_items = db.scalars(stmt).all()
    total = len(all_items)
    paged = all_items[(page - 1) * page_size:page * page_size]
    return jsonify({
        "total": total, "page": page, "page_size": page_size,
        "items": [{
            "id": s.id, "scan_type": s.scan_type, "trust_score": s.trust_score,
            "risk_level": s.risk_level, "summary": s.summary, "status": s.status,
            "user_id": s.user_id, "is_public": s.is_public,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        } for s in paged],
    })
