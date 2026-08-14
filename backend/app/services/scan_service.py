"""Scan orchestration service.

Runs a scanner, scores findings with the trust engine, persists the scan,
checks known threats, creates a report and sends notifications.
"""
from __future__ import annotations

import logging
import re
from typing import Any

from sqlalchemy.orm import Session

from app.models import Scan, User
from app.repositories.admin_repo import ThreatRepository, ThreatReportRepository
from app.repositories.notification_repo import NotificationRepository
from app.repositories.scan_repo import ScanRepository
from app.services import email_scanner, file_scanner, image_scanner, qr_scanner
from app.services import text_scanner, url_scanner
from app.trust_engine.engine import EngineResult, compute_trust_score

logger = logging.getLogger("aegis.scan")

SCANNERS: dict[str, Any] = {
    "url": url_scanner._scan_url_sync,
    "text": text_scanner._scan_text_sync,
    "email": email_scanner._scan_email_sync,
    "file": file_scanner._scan_file_sync,
    "image": image_scanner._scan_image_sync,
    "qr": qr_scanner._scan_qr_sync,
}

SCAN_LABELS = {
    "url": "Website",
    "text": "Message",
    "email": "Email",
    "file": "File",
    "image": "Screenshot",
    "qr": "QR code",
}


def _scanner_kwargs(scan_type: str, scan: Scan) -> dict:
    if scan_type == "url":
        return {"url": scan.input_url or scan.input_text}
    if scan_type == "text":
        return {"text": scan.input_text or ""}
    if scan_type == "email":
        return {"raw": scan.input_text or ""}
    if scan_type == "file":
        return {"file_path": scan.file_path or "", "filename": scan.file_name or "", "mime": scan.file_mime}
    if scan_type == "image":
        return {"image_bytes": _read_file(scan.file_path)}
    if scan_type == "qr":
        return {"image_bytes": _read_file(scan.file_path)}
    raise ValueError(f"Unsupported scan type {scan_type}")


def _read_file(path: str | None) -> bytes:
    if not path:
        raise ValueError("Uploaded file is missing")
    with open(path, "rb") as fh:
        return fh.read()


def _threat_candidates(scan_type: str, scan: Scan) -> list[str]:
    """Values to check against the known-threat database."""
    if scan_type == "url":
        return [scan.input_url or ""]
    if scan_type in ("text", "email", "file"):
        urls = re.findall(r"https?://[^\s<>'\"\]]+", scan.input_text or "")
        return urls[:10]
    return []


def run_scan(
    db: Session,
    scan_type: str,
    data: dict,
    user: User | None = None,
    ip: str | None = None,
    geo: dict | None = None,
    is_public: bool = False,
    save_history: bool | None = None,
) -> Scan:
    """Execute a full scan and persist the outcome (synchronous)."""
    scan_repo = ScanRepository(db)
    threat_repo = ThreatRepository(db)
    notify_repo = NotificationRepository(db)

    create_data = {
        "scan_type": scan_type,
        "input_text": data.get("input_text"),
        "input_url": data.get("input_url"),
        "file_path": data.get("file_path"),
        "file_name": data.get("file_name"),
        "file_mime": data.get("file_mime"),
        "is_public": is_public,
        "ip_address": ip,
    }
    if user:
        create_data["user_id"] = user.id
    if geo:
        create_data.update({
            "country": geo.get("country"),
            "country_name": geo.get("country_name"),
            "latitude": geo.get("latitude"),
            "longitude": geo.get("longitude"),
        })
    scan = scan_repo.create(create_data)

    known: list = []
    try:
        scanner = SCANNERS[scan_type]
        kwargs = _scanner_kwargs(scan_type, scan)

        if scan_type == "url":
            candidates = [c for c in _threat_candidates(scan_type, scan) if c]
            known = threat_repo.match_any(candidates)
            kwargs["known_threats"] = [t.value for t in known]

        raw_result = scanner(**kwargs)
        findings = raw_result.get("findings", [])

        for threat in known:
            threat_repo.increment_hit(threat)
            if not any(f.get("code") == "known_threat" for f in findings):
                findings.append({
                    "code": "known_threat", "category": "reputation",
                    "title": "Known threat match",
                    "description": "This address is already known to be malicious.",
                    "severity": "critical", "evidence": threat.value,
                    "confidence": 0.99, "impact": 0.0,
                })

        ai_conf = raw_result.get("meta", {}).get("ai_probability")
        ai_label = raw_result.get("meta", {}).get("ai_label")

        engine: EngineResult = compute_trust_score(
            findings, db=db, ai_confidence=ai_conf, ai_label=ai_label
        )

        # Persist the calibrated contribution that the user sees in the report.
        # Scanner findings retain their raw provenance in ``extra``; the engine
        # contribution is the explainable, correlation-aware display impact.
        reason_by_code = {reason.code: reason for reason in engine.reasons}
        for finding in findings:
            reason = reason_by_code.get(finding.get("code"))
            if reason:
                finding["impact"] = reason.impact
                finding["confidence"] = reason.confidence
                extra = dict(finding.get("extra") or {})
                extra.update({
                    "engine_version": engine.engine_version,
                    "engine_impact": reason.impact,
                    "occurrences": reason.occurrences,
                })
                finding["extra"] = extra
            scan_repo.add_finding(scan.id, finding)

        summary = _build_summary(scan_type, engine, raw_result.get("meta", {}))
        scan_repo.complete(scan, engine.trust_score, engine.risk_level,
                           engine.confidence, summary)

        scan_repo.save_report(
            scan=scan,
            title=f"{SCAN_LABELS.get(scan_type, 'Scan')} analysis report",
            summary=summary,
            recommendation=_recommendation_text(engine),
            highlights=engine.highlights,
            timeline=_build_timeline(scan_type, engine),
            user_id=user.id if user else None,
        )

        if engine.risk_level in ("high", "critical") and user:
            notify_repo.create(
                user_id=user.id,
                title=f"{engine.risk_level.title()} risk detected",
                body=f"{SCAN_LABELS.get(scan_type, 'Scan')} scored {engine.trust_score}/100.",
                kind="scan_alert",
                link=f"/report/{scan.id}",
            )

        # Public reporting is explicit on the submitted scan. A remembered
        # account setting must never silently publish content or derived location.
        if is_public:
            _submit_geo_report(db, scan, engine)

        db.commit()
        db.refresh(scan)
        return scan
    except Exception as exc:
        db.rollback()
        scan.status = "failed"
        scan.summary = f"Scan failed: {exc}"
        db.add(scan)
        db.commit()
        logger.exception("scan failed type=%s", scan_type)
        raise


def _submit_geo_report(db: Session, scan: Scan, engine: EngineResult) -> None:
    if not (scan.latitude and scan.longitude):
        return
    report_repo = ThreatReportRepository(db)
    report_repo.create({
        "user_id": scan.user_id,
        "scan_id": scan.id,
        "content_type": scan.scan_type,
        "content": (scan.input_url or scan.input_text or scan.file_name or "")[:500],
        "category": engine.risk_level,
        "country": scan.country,
        "country_name": scan.country_name,
        "latitude": scan.latitude,
        "longitude": scan.longitude,
    })


def _build_summary(scan_type: str, engine: EngineResult, meta: dict) -> str:
    label = SCAN_LABELS.get(scan_type, "content")
    if engine.risk_level == "low":
        base = f"The {label.lower()} appears to be safe."
    elif engine.risk_level == "medium":
        base = f"The {label.lower()} shows some warning signs."
    elif engine.risk_level == "high":
        base = f"The {label.lower()} shows strong signs of a scam."
    else:
        base = f"The {label.lower()} is very likely a scam."
    return (
        f"{base} Trust score {engine.trust_score}/100, estimated risk "
        f"{engine.risk_probability:.0%}, evidence confidence {engine.confidence:.0%}."
    )


def _recommendation_text(engine: EngineResult) -> str:
    return "\n".join(engine.recommendations[:6])


def _build_timeline(scan_type: str, engine: EngineResult) -> list[dict]:
    return [
        {"step": "Input received", "detail": f"{SCAN_LABELS.get(scan_type, 'Content')} captured for analysis"},
        {"step": "Indicator analysis", "detail": f"{len(engine.reasons)} indicators evaluated"},
        {"step": "Evidence fused", "detail": f"Score {engine.trust_score}/100 ({engine.risk_level} risk; confidence {engine.confidence:.0%})"},
        {"step": "Recommendations generated", "detail": f"{len(engine.recommendations)} actionable tips"},
    ]


def _verdict_for(risk_level: str) -> str:
    if risk_level in ("high", "critical"):
        return "threat"
    if risk_level == "medium":
        return "suspicious"
    return "safe"


def scan_to_dict(scan: Scan) -> dict:
    """Serialize a completed Scan for the API and report pages."""
    target = scan.input_url or scan.input_text or scan.file_name or ""
    reasons = [{
        "reason": (f.title or f.code or "Signal"),
        "impact": f.impact or 0.0,
        "confidence": f.confidence or 0.0,
    } for f in scan.findings]
    recommendations = []
    highlights = []
    if scan.report:
        recommendations = [
            line.strip() for line in (scan.report.recommendation or "").splitlines()
            if line.strip()
        ]
        highlights = scan.report.highlights or []
    if not highlights:
        highlights = [
            f.evidence for f in scan.findings
            if f.severity in ("high", "critical") and f.evidence
        ][:6]
    return {
        "id": scan.id,
        "scan_id": scan.id,
        "target": target,
        "scan_type": scan.scan_type,
        "trust_score": scan.trust_score,
        "risk_level": scan.risk_level,
        "verdict": _verdict_for(scan.risk_level),
        "confidence": scan.confidence,
        "summary": scan.summary,
        "status": scan.status,
        "model_used": "evidence-fusion-v2",
        "reasons": reasons,
        "recommendations": recommendations,
        "highlights": highlights,
        "findings": [f.to_dict() for f in scan.findings],
        "country": scan.country,
        "country_name": scan.country_name,
        "latitude": scan.latitude,
        "longitude": scan.longitude,
        "is_public": scan.is_public,
        "created_at": scan.created_at.isoformat() if scan.created_at else None,
        "completed_at": scan.completed_at.isoformat() if scan.completed_at else None,
    }
