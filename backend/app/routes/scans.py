"""Scan API blueprint: run scanners, history, bookmarks, reports, PDF."""
from __future__ import annotations

import base64
import binascii
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
from app.security.sanitize import sanitize_filename
from app.services import geo_service, scan_service
from app.services.report_service import generate_pdf

bp = Blueprint("scans_api", __name__, url_prefix="/api/v1/scans")

ALLOWED_IMAGE = settings.allowed_image_ext
ALLOWED_FILES = settings.allowed_file_ext
MAX_UPLOAD = settings.max_upload_mb * 1024 * 1024


def _geo_from_request() -> dict:
    ip = None
    forwarded = request.headers.get("x-forwarded-for")
    ip = forwarded.split(",")[0].strip() if forwarded else request.remote_addr
    geo = geo_service.lookup(ip)
    return {**geo, "ip": ip}


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
    return jsonify(scan_service.scan_to_dict(scan))


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
    return jsonify(scan_service.scan_to_dict(scan))


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
    return jsonify(scan_service.scan_to_dict(scan))


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
    return jsonify(_run_uploaded("image", saved))


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
    return jsonify(_run_uploaded("qr", saved))


@bp.post("/file")
@optional_login
def scan_file():
    file = request.files.get("file")
    if file is None:
        raise ValidationError("Provide a file")
    saved = _save_upload(file, "file")
    return jsonify(_run_uploaded("file", saved))


def _save_bytes(data: bytes, name: str, mime: str, kind: str) -> dict:
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
    return scan_service.scan_to_dict(scan)


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


@bp.get("/<int:scan_id>/incident-packet")
@optional_login
def incident_packet(scan_id: int):
    """Return a structured response packet for a permitted scan.

    This does not claim external confirmation. It packages the engine's own
    evidence, its version, and the user-facing containment steps so a team can
    attach it to a case-management or SIEM workflow without reinterpreting the
    score as an opaque model verdict.
    """
    scan, repo = _get_scan_or_404(scan_id)
    if not _allowed_to_view(scan):
        raise NotFoundError("Scan not found")
    report = repo.get_report(scan_id)
    findings = [finding.to_dict() for finding in scan.findings]
    indicators = []
    for finding in findings:
        extra = finding.get("extra") or {}
        indicators.append({
            "code": finding.get("code"), "title": finding.get("title"),
            "severity": finding.get("severity"), "confidence": finding.get("confidence"),
            "evidence": finding.get("evidence"), "source": extra.get("source", "scanner_observation"),
            "engine_impact": extra.get("engine_impact", finding.get("impact")),
        })
    recommendations = (report.recommendation or "").splitlines() if report and report.recommendation else []
    return jsonify({
        "case_id": f"AEGIS-{scan.id}",
        "created_at": scan.created_at.isoformat() if scan.created_at else None,
        "classification": {
            "risk_level": scan.risk_level, "trust_score": scan.trust_score,
            "evidence_confidence": scan.confidence,
            "engine": "evidence-fusion-v2",
            "interpretation": "Evidence confidence reflects coverage and agreement; it is not measured predictive accuracy.",
        },
        "target": scan.input_url or scan.input_text or scan.file_name,
        "scan_type": scan.scan_type,
        "evidence": indicators,
        "containment_actions": [item for item in recommendations if item.strip()],
        "report_summary": report.summary if report else scan.summary,
        "provenance": {
            "generated_by": "AEGIS deterministic evidence fusion",
            "external_intelligence": sorted({item["source"] for item in indicators if str(item["source"]).startswith("feed:")}),
            "network_acquisition": next((f.get("extra", {}).get("network_fetch") for f in findings if f.get("code") == "unsafe_destination"), "not_applicable"),
        },
    })


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
