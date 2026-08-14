"""QR analyzer: decode QR codes and analyze the destination."""
from __future__ import annotations

import asyncio

from app.ai.url_analysis import is_ip_address, is_shortened, detect_typosquatting, SUSPICIOUS_TLDS, extract_tld
from app.ocr.qr import decode_qr
from app.services.text_scanner import _scan_text_sync


async def scan_qr(image_bytes: bytes) -> dict:
    return await asyncio.to_thread(_scan_qr_sync, image_bytes)


def _scan_qr_sync(image_bytes: bytes) -> dict:
    codes = decode_qr(image_bytes)
    if not codes:
        return {
            "findings": [{
                "code": "qr_not_found", "category": "analysis",
                "title": "No QR code detected",
                "description": "No QR code could be detected in the uploaded image.",
                "evidence": None, "severity": "info", "impact": 0.0, "confidence": 0.9,
            }],
            "meta": {"decoded": [], "count": 0},
        }

    decoded = []
    findings: list[dict] = []

    def add(code, category, title, description, severity, evidence=None, confidence=0.8):
        findings.append({
            "code": code, "category": category, "title": title,
            "description": description, "severity": severity,
            "evidence": evidence, "impact": 0.0, "confidence": confidence,
        })

    for code in codes[:3]:
        content = code["content"]
        entry = {"content": content[:500], "format": code["format"]}

        if content.startswith(("http://", "https://")):
            from urllib.parse import urlparse

            parsed = urlparse(content)
            host = (parsed.hostname or "").lower()
            short, hostname = is_shortened(content)
            if short:
                add("shortened_url", "obfuscation", "Shortened QR destination",
                    "The QR code points to a shortened link hiding its destination.",
                    "low", content, 0.9)
            if is_ip_address(host):
                add("ip_address_url", "obfuscation", "IP address destination",
                    "The QR code points directly to an IP address.",
                    "high", content, 0.9)
            brand, _ = detect_typosquatting(host)
            if brand:
                add("typosquatting", "impersonation", "Typosquatting destination",
                    f"The QR destination imitates the brand '{brand}'.",
                    "critical", content, 0.9)
            tld = extract_tld(host)
            if tld in SUSPICIOUS_TLDS:
                add("suspicious_tld", "reputation", "Suspicious TLD destination",
                    "The QR destination uses a TLD frequently abused by scammers.",
                    "medium", content, 0.8)
            entry["kind"] = "url"
        else:
            # Non-URL content - analyze as text
            text_result = _scan_text_sync(content[:4000])
            findings.extend(text_result["findings"])
            entry["kind"] = "text"

        decoded.append(entry)

    return {
        "findings": findings,
        "meta": {
            "decoded": decoded,
            "count": len(decoded),
            "decode_confidence": 0.9,
        },
    }
