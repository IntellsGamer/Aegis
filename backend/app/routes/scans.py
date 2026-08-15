"""Scan API blueprint: run scanners, history, bookmarks, reports, PDF."""
from __future__ import annotations

import base64
import binascii
import hashlib
import json
import mimetypes
import os
import re
import tempfile
from datetime import datetime
from pathlib import Path

from flask import Blueprint, jsonify, request, send_file, abort

from app.config import settings
from app.dependencies import db_session, login_required, optional_login
from app.exceptions import APIError, NotFoundError, ValidationError
from app.repositories.scan_repo import ScanRepository
from app.schemas.scan import ScanOut, EmailScanRequest, TextScanRequest, UrlScanRequest
from app.security.file_safety import UnsafeUpload, inspect_upload
from app.security.sanitize import sanitize_filename
from app.services import geo_service, scan_service
from app.services.report_service import generate_pdf

bp = Blueprint("scans_api", __name__, url_prefix="/api/v1/scans")

ALLOWED_IMAGE = settings.allowed_image_ext
ALLOWED_FILES = settings.allowed_file_ext
MAX_UPLOAD = settings.max_upload_mb * 1024 * 1024


def _geo_from_request() -> dict:
    forwarded = request.headers.get("x-forwarded-for")
    ip = forwarded.split(",")[0].strip() if forwarded else request.remote_addr
    # When AEGIS runs behind Cloudflare, its country header is already coarse
    # enough for the approved-report map and avoids a second geo lookup. Unknown
    # values are intentionally ignored; no fallback country is invented.
    cloudflare_country = (request.headers.get("cf-ipcountry") or "").strip().upper()
    if cloudflare_country and cloudflare_country != "XX" and geo_service.country_centroid(cloudflare_country):
        return {
            "country": cloudflare_country,
            "country_name": geo_service.country_name(cloudflare_country),
            "location_precision": "cloudflare_country",
            "ip": ip,
        }
    geo = geo_service.lookup(ip)
    if geo:
        return {**geo, "ip": ip}
    # Loopback/private traffic has no genuine GeoIP answer. In development only,
    # attach the explicitly configured demo country so local moderation and map
    # behavior can be exercised without claiming a real client location.
    return {**geo_service.development_country(ip), "ip": ip}


def _report_location(scan) -> dict:
    """Return persisted country data, or an explicit development demo fallback."""
    if scan.country:
        return {"country": scan.country, "country_name": scan.country_name}
    demo = geo_service.development_country(scan.ip_address)
    if demo:
        # Preserve this explicit local-demo origin on the scan as well, so later
        # feedback and casefile views consistently describe map eligibility.
        scan.country = demo["country"]
        scan.country_name = demo["country_name"]
        db_session().add(scan)
        db_session().flush()
    return demo


def _validate_json(schema_class, extra_none_keys=()):
    data = request.get_json(silent=True) or {}
    try:
        payload = schema_class(**data)
    except Exception as exc:
        errors = getattr(exc, "errors", lambda: [])()
        if errors:
            first = errors[0]
            loc = ".".join(str(x) for x in first.get("loc", []))
            raise ValidationError(f"{loc}: {first.get('msg', 'invalid value')}")
        raise ValidationError(str(exc))
    return payload


def _save_upload(file_storage, scan_type: str) -> dict:
    filename = file_storage.filename or ""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    allowed = ALLOWED_IMAGE if scan_type in ("image", "qr") else ALLOWED_FILES
    if ext not in allowed:
        raise ValidationError(f"File type '.{ext}' is not allowed for {scan_type} scans")
    content = file_storage.read()
    if len(content) > MAX_UPLOAD:
        raise APIError(f"File exceeds {settings.max_upload_mb} MB limit", status_code=413)
    try:
        inspect_upload(content, filename or f"upload.{ext}", scan_type)
    except UnsafeUpload as exc:
        raise ValidationError(str(exc)) from exc
    upload_dir = Path(settings.upload_dir) / scan_type
    upload_dir.mkdir(parents=True, exist_ok=True)
    safe_name = sanitize_filename(filename or f"upload.{ext}")
    path = upload_dir / f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{os.urandom(3).hex()}-{safe_name}"
    path.write_bytes(content)
    return {
        "file_path": str(path),
        "file_name": safe_name,
        "file_mime": file_storage.mimetype or mimetypes.guess_type(safe_name)[0],
    }


def _decode_data_uri(data_uri: str) -> bytes:
    if "," in data_uri:
        data_uri = data_uri.split(",", 1)[1]
    try:
        return base64.b64decode(data_uri, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValidationError("Invalid base64 image data") from exc


def _get_scan_or_404(scan_id: int):
    repo = ScanRepository(db_session())
    scan = repo.get(scan_id)
    if not scan:
        raise NotFoundError("Scan not found")
    return scan, repo


def _allowed_to_view(scan) -> bool:
    from app.dependencies import current_user

    if scan.is_public:
        return True
    user = current_user()
    return bool(user and scan.user_id == user.id)


def _response_with_retention(scan, user, save_history: bool | None = None):
    """Serialize a result, then purge it when the caller did not opt into storage."""
    payload = scan_service.scan_to_dict(scan)
    keep_history = scan.is_public or (
        bool(save_history) if save_history is not None
        else bool(user and getattr(user, "settings", None) and user.settings.save_history)
    )
    if keep_history:
        payload["retention"] = "stored"
        return jsonify(payload)

    # A result can be delivered from the active transaction without retaining
    # the message, URL, findings, report, location, or uploaded artifact.
    file_path = scan.file_path
    db_session().delete(scan)
    db_session().commit()
    if file_path:
        try:
            Path(file_path).unlink(missing_ok=True)
        except OSError:
            pass
    payload["retention"] = "not_stored"
    payload["scan_id"] = None
    payload["id"] = None
    return jsonify(payload)


# --------------------------------------------------------------------------
# Scan execution
# --------------------------------------------------------------------------
@bp.post("/url")
@optional_login
def scan_url():
    payload = _validate_json(UrlScanRequest)
    url = payload.url.strip()
    if not re.match(r"^https?://", url, re.IGNORECASE):
        url = "https://" + url
    from app.utils.validators import is_valid_url, normalize_url

    if not is_valid_url(url):
        raise ValidationError("Please provide a valid http(s) URL")
    from app.dependencies import current_user

    user = current_user()
    geo = _geo_from_request()
    scan = scan_service.run_scan(
        db_session(), "url", {"input_url": normalize_url(url)},
        user=user, ip=geo.pop("ip", None), geo=geo, is_public=payload.is_public,
        save_history=payload.save_history,
    )
    return _response_with_retention(scan, user, payload.save_history)


@bp.post("/text")
@optional_login
def scan_text():
    payload = _validate_json(TextScanRequest)
    from app.dependencies import current_user

    user = current_user()
    geo = _geo_from_request()
    scan = scan_service.run_scan(
        db_session(), "text", {"input_text": payload.text},
        user=user, ip=geo.pop("ip", None), geo=geo, is_public=payload.is_public,
        save_history=payload.save_history,
    )
    return _response_with_retention(scan, user, payload.save_history)


@bp.post("/email")
@optional_login
def scan_email():
    payload = _validate_json(EmailScanRequest)
    from app.dependencies import current_user

    user = current_user()
    geo = _geo_from_request()
    scan = scan_service.run_scan(
        db_session(), "email", {"input_text": payload.raw_email},
        user=user, ip=geo.pop("ip", None), geo=geo, is_public=payload.is_public,
        save_history=payload.save_history,
    )
    return _response_with_retention(scan, user, payload.save_history)


@bp.post("/image")
@optional_login
def scan_image():
    file = request.files.get("file")
    image_data = request.form.get("image")
    if file is None and not image_data:
        raise ValidationError("Provide an image file or base64 data")
    if file is not None:
        saved = _save_upload(file, "image")
    else:
        data = _decode_data_uri(image_data)
        saved = _save_bytes(data, "image.png", "image/png", "image")
    return _run_uploaded("image", saved)


@bp.post("/qr")
@optional_login
def scan_qr():
    file = request.files.get("file")
    image_data = request.form.get("image")
    if file is None and not image_data:
        raise ValidationError("Provide a QR image file or base64 data")
    if file is not None:
        saved = _save_upload(file, "qr")
    else:
        data = _decode_data_uri(image_data)
        saved = _save_bytes(data, "qr.png", "image/png", "qr")
    return _run_uploaded("qr", saved)


@bp.post("/file")
@optional_login
def scan_file():
    file = request.files.get("file")
    if file is None:
        raise ValidationError("Provide a file")
    saved = _save_upload(file, "file")
    return _run_uploaded("file", saved)


def _save_bytes(data: bytes, name: str, mime: str, kind: str) -> dict:
    try:
        inspect_upload(data, name, kind)
    except UnsafeUpload as exc:
        raise ValidationError(str(exc)) from exc
    upload_dir = Path(settings.upload_dir) / kind
    upload_dir.mkdir(parents=True, exist_ok=True)
    path = upload_dir / f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{os.urandom(3).hex()}-{name}"
    path.write_bytes(data)
    return {"file_path": str(path), "file_name": name, "file_mime": mime}


def _run_uploaded(scan_type: str, saved: dict):
    from app.dependencies import current_user

    user = current_user()
    geo = _geo_from_request()
    scan = scan_service.run_scan(
        db_session(), scan_type, saved,
        user=user, ip=geo.pop("ip", None), geo=geo,
        is_public=request.form.get("is_public") == "true",
    )
    raw_save_history = request.form.get("save_history")
    save_history = None if raw_save_history is None else raw_save_history.lower() == "true"
    return _response_with_retention(scan, user, save_history)


# --------------------------------------------------------------------------
# History / bookmarks / reports
# --------------------------------------------------------------------------
@bp.get("")
@login_required
def list_scans():
    from app.dependencies import current_user
    user = current_user()
    page = request.args.get("page", 1, type=int)
    page_size = min(request.args.get("page_size", 20, type=int), 100)
    scan_type = request.args.get("scan_type")
    risk = request.args.get("risk")
    repo = ScanRepository(db_session())
    total, items = repo.list_for_user(user.id, page, page_size, scan_type, risk)
    return jsonify({
        "total": total, "page": page, "page_size": page_size,
        "items": [scan_service.scan_to_dict(s) for s in items],
    })


@bp.get("/public")
def list_public():
    page = request.args.get("page", 1, type=int)
    page_size = min(request.args.get("page_size", 20, type=int), 100)
    repo = ScanRepository(db_session())
    total, items = repo.list_public(page, page_size)
    return jsonify({
        "total": total, "page": page, "page_size": page_size,
        "items": [scan_service.scan_to_dict(s) for s in items],
    })


@bp.get("/<int:scan_id>")
@optional_login
def get_scan(scan_id: int):
    scan, _ = _get_scan_or_404(scan_id)
    if not _allowed_to_view(scan):
        raise NotFoundError("Scan not found")
    return jsonify(scan_service.scan_to_dict(scan))


@bp.delete("/<int:scan_id>")
@login_required
def delete_scan(scan_id: int):
    from app.dependencies import current_user

    repo = ScanRepository(db_session())
    scan = repo.get_for_user(scan_id, current_user().id)
    if not scan:
        raise NotFoundError("Scan not found")
    repo.delete(scan)
    return jsonify({"detail": "Scan deleted"})


@bp.get("/bookmarks")
@login_required
def bookmarks():
    from app.dependencies import current_user

    repo = ScanRepository(db_session())
    items = repo.list_bookmarks(current_user().id)
    return jsonify({"total": len(items), "items": [scan_service.scan_to_dict(s) for s in items]})


@bp.post("/<int:scan_id>/bookmark")
@login_required
def toggle_bookmark(scan_id: int):
    from app.dependencies import current_user

    scan, repo = _get_scan_or_404(scan_id)
    if not _allowed_to_view(scan):
        raise NotFoundError("Scan not found")
    bookmarked = repo.toggle_bookmark(scan, current_user())
    return jsonify({"bookmarked": bookmarked})


@bp.get("/<int:scan_id>/report")
@optional_login
def get_report(scan_id: int):
    scan, repo = _get_scan_or_404(scan_id)
    if not _allowed_to_view(scan):
        raise NotFoundError("Scan not found")
    report = repo.get_report(scan_id)
    return jsonify({
        "scan": scan_service.scan_to_dict(scan),
        "report": {
            "title": report.title if report else None,
            "summary": report.summary if report else None,
            "recommendation": report.recommendation if report else None,
            "highlights": report.highlights if report else [],
            "timeline": report.timeline if report else [],
        } if report else None,
    })


@bp.post("/<int:scan_id>/feedback")
@login_required
def submit_scan_feedback(scan_id: int):
    """Record a user-confirmed outcome for a scan they own.

    Outcomes are kept separate from the deterministic engine and are used for
    measured review, not automatic model training or rule rewrites.
    """
    from app.dependencies import current_user
    from app.repositories.admin_repo import ThreatReportRepository
    from app.repositories.governance_repo import GovernanceRepository

    scan, _ = _get_scan_or_404(scan_id)
    user = current_user()
    if scan.user_id != user.id:
        raise NotFoundError("Scan not found")
    data = request.get_json(silent=True) or {}
    try:
        outcome = GovernanceRepository(db_session()).record_outcome(
            scan=scan,
            reviewer_user_id=user.id,
            verdict=str(data.get("verdict") or ""),
            rationale=(data.get("rationale") or "")[:2000] or None,
            engine_version="evidence-fusion-v2",
            evidence_snapshot={
                "source": "user_feedback", "trust_score": scan.trust_score,
                "risk_level": scan.risk_level, "confidence": scan.confidence,
            },
        )
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc

    triage_report = None
    triage_created = False
    if outcome.verdict == "confirmed_malicious":
        reports = ThreatReportRepository(db_session())
        triage_report = reports.get_for_scan(scan.id)
        if triage_report is None:
            content = (scan.input_url or scan.input_text or scan.file_name or f"AEGIS assessment {scan.id}").strip()
            report_location = _report_location(scan)
            triage_report = reports.create({
                "user_id": user.id,
                "scan_id": scan.id,
                "content_type": scan.scan_type,
                "content": content[:500],
                "category": "phishing",
                "description": (
                    f"User-confirmed malicious assessment {scan.id}. "
                    f"{(data.get('rationale') or scan.summary or '')[:850]}"
                ).strip(),
                "country": report_location.get("country"),
                "country_name": report_location.get("country_name"),
                "latitude": None,
                "longitude": None,
            })
            triage_created = True

    response = {"id": outcome.id, "verdict": outcome.verdict, "detail": "Feedback recorded"}
    if triage_report:
        development_location = geo_service.development_country(scan.ip_address)
        is_development_demo = bool(
            development_location
            and triage_report.country == development_location.get("country")
        )
        response["triage_report"] = {
            "id": triage_report.id,
            "status": triage_report.status,
            "created": triage_created,
            "map_eligible_after_approval": bool(triage_report.country),
            "development_demo_location": is_development_demo,
            "country": triage_report.country,
        }
    return jsonify(response), 201


def _build_casefile(scan, repo) -> dict:
    """Build a reviewable, self-contained record from a persisted scan.

    The payload intentionally distinguishes locally observed evidence, opted-in
    intelligence sources, and coverage limits. Its fingerprint is an integrity
    aid for exported content, not a signature or a claim of external validation.
    """
    report = repo.get_report(scan.id)
    scan_data = scan_service.scan_to_dict(scan)
    findings = [finding.to_dict() for finding in scan.findings]
    evidence = []
    families: dict[str, dict] = {}
    for finding in findings:
        extra = finding.get("extra") or {}
        category = finding.get("category") or "other"
        impact = float(extra.get("engine_impact", finding.get("impact") or 0.0))
        evidence.append({
            "code": finding.get("code"), "title": finding.get("title"),
            "description": finding.get("description"), "category": category,
            "severity": finding.get("severity"), "confidence": finding.get("confidence"),
            "evidence": finding.get("evidence"), "source": extra.get("source", "scanner_observation"),
            "engine_impact": impact,
            "observation_scope": "local" if str(extra.get("source", "")).startswith("local_") else "assessment",
        })
        family = families.setdefault(category, {"family": category, "signals": 0, "net_impact": 0.0})
        family["signals"] += 1
        family["net_impact"] += impact
    for family in families.values():
        family["net_impact"] = round(family["net_impact"], 2)

    limitations = [
        "Evidence confidence describes collection coverage and cross-family agreement; it is not measured predictive accuracy.",
        "A casefile records this assessment only. It does not establish criminal attribution or external confirmation.",
    ]
    state = scan_data["assessment_state"]
    if state == "limited":
        limitations.insert(0, "Remote destination checks were not completed because the hostname could not be resolved.")
    elif state == "blocked":
        limitations.insert(0, "The destination was not probed because it crossed AEGIS network-safety boundaries.")

    recommendations = [line.strip() for line in (report.recommendation or "").splitlines() if line.strip()] if report else []
    response_playbook = [{"phase": "Contain", "action": action, "owner": "User or service desk"} for action in recommendations]
    external_sources = sorted({item["source"] for item in evidence if str(item["source"]).startswith("feed:")})
    finding_codes = {item.get("code") for item in evidence}
    if "destination_unresolved" in finding_codes:
        network_acquisition = "not_attempted"
    elif "unsafe_destination" in finding_codes:
        network_acquisition = "blocked"
    elif scan.scan_type == "url" and state == "complete":
        network_acquisition = "completed"
    else:
        network_acquisition = "not_applicable"
    payload = {
        "case_id": f"AEGIS-{scan.id}",
        "created_at": scan.created_at.isoformat() if scan.created_at else None,
        "classification": {
            "assessment_state": state, "verdict": scan_data["verdict"], "risk_level": scan.risk_level,
            "trust_score": scan.trust_score, "evidence_confidence": scan.confidence,
            "engine": "evidence-fusion-v2",
            "interpretation": "Evidence confidence reflects coverage and agreement; it is not measured predictive accuracy.",
        },
        "target": scan_data["target"], "scan_type": scan.scan_type,
        "evidence": evidence,
        "evidence_families": sorted(families.values(), key=lambda item: abs(item["net_impact"]), reverse=True),
        "containment_actions": recommendations,
        "response_playbook": response_playbook,
        "timeline": report.timeline if report and report.timeline else [],
        "limitations": limitations,
        "report_summary": report.summary if report else scan.summary,
        "provenance": {
            "generated_by": "AEGIS deterministic evidence fusion",
            "training_boundary": "No model training or automatic rule changes are performed from this casefile or feedback.",
            "external_intelligence": external_sources,
            "network_acquisition": network_acquisition,
            "retention": "Stored at the account holder's explicit history preference when this casefile exists.",
        },
    }
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    payload["integrity"] = {
        "algorithm": "SHA-256", "fingerprint": hashlib.sha256(canonical).hexdigest(),
        "scope": "Canonical casefile payload before this integrity field; fingerprint is not a digital signature.",
    }
    return payload


@bp.get("/<int:scan_id>/casefile")
@optional_login
def casefile(scan_id: int):
    scan, repo = _get_scan_or_404(scan_id)
    if not _allowed_to_view(scan):
        raise NotFoundError("Scan not found")
    return jsonify(_build_casefile(scan, repo))


@bp.get("/<int:scan_id>/incident-packet")
@optional_login
def incident_packet(scan_id: int):
    """Compatibility endpoint for teams integrating an AEGIS casefile."""
    scan, repo = _get_scan_or_404(scan_id)
    if not _allowed_to_view(scan):
        raise NotFoundError("Scan not found")
    return jsonify(_build_casefile(scan, repo))


@bp.get("/<int:scan_id>/report.pdf")
@optional_login
def export_pdf(scan_id: int):
    scan, repo = _get_scan_or_404(scan_id)
    if not _allowed_to_view(scan):
        raise NotFoundError("Scan not found")
    report = repo.get_report(scan_id)
    reasons = [f.to_dict() for f in scan.findings]
    recommendations = (
        (report.recommendation or "").splitlines()
        if report and report.recommendation
        else []
    )
    pdf = generate_pdf(scan, reasons, recommendations)
    if pdf is None:
        raise APIError("PDF export is unavailable (ReportLab not installed)", status_code=503)
    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    tmp.write(pdf)
    tmp.close()
    return send_file(
        tmp.name, mimetype="application/pdf",
        as_attachment=True, download_name=f"aegis-report-{scan.id}.pdf",
    )
