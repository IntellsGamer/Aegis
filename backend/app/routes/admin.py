"""Admin API blueprint: users, threats, keywords, rules, logs, retraining."""
from __future__ import annotations

import re

from flask import Blueprint, jsonify, request

from app.ai.model_manager import model_manager
from app.dependencies import admin_required, db_session
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
from app.services.notification_service import create_and_notify

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
# Model retraining
# --------------------------------------------------------------------------
@bp.post("/models/retrain")
@admin_required
def retrain():
    try:
        metrics = model_manager.train_all()
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400
    create_and_notify(db_session(), None, "Model retrained",
                      "The AI classifiers were retrained on the latest dataset.",
                      kind="system")
    return jsonify({"status": "ok", "metrics": metrics})


@bp.get("/models/info")
@admin_required
def model_info():
    return jsonify(model_manager.capabilities())


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
