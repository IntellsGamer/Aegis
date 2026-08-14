"""Image analyzer: OCR the screenshot, then analyze the extracted text.

Also classifies whether the image resembles a login page, bank screen,
QR code, scam message or payment request.
"""
from __future__ import annotations

import asyncio

from app.ocr.service import extract_text


async def scan_image(image_bytes: bytes) -> dict:
    return await asyncio.to_thread(_scan_image_sync, image_bytes)


def _classify_text(text: str) -> list[dict]:
    findings = []
    lower = text.lower()
    if any(k in lower for k in ("username", "password", "log in", "sign in", "login")):
        findings.append({
            "code": "login_form", "category": "credential",
            "title": "Fake login page",
            "description": "The screenshot appears to be a login page that could capture credentials.",
            "evidence": None, "severity": "high", "impact": 0.0, "confidence": 0.8,
        })
    if any(k in lower for k in ("card number", "cvv", "card details", "pay now", "payment")):
        findings.append({
            "code": "payment_request", "category": "credential",
            "title": "Fake payment request",
            "description": "The screenshot requests payment or card details.",
            "evidence": None, "severity": "high", "impact": 0.0, "confidence": 0.8,
        })
    if any(k in lower for k in ("verification code", "otp", "one-time password", "security code")):
        findings.append({
            "code": "requests_otp", "category": "credential",
            "title": "Verification code request",
            "description": "The screenshot asks for a verification or one-time code.",
            "evidence": None, "severity": "critical", "impact": 0.0, "confidence": 0.8,
        })
    if any(k in lower for k in ("your bank", "bank of", "online banking", "visa", "mastercard")):
        findings.append({
            "code": "bank_impersonation", "category": "impersonation",
            "title": "Bank screenshot",
            "description": "The screenshot appears to be from a bank or financial service.",
            "evidence": None, "severity": "high", "impact": 0.0, "confidence": 0.7,
        })
    return findings


def _scan_image_sync(image_bytes: bytes) -> dict:
    ocr = extract_text(image_bytes)
    text = ocr.get("text", "")

    from app.services.text_scanner import _scan_text_sync

    text_result = _scan_text_sync(text) if text else {"findings": [], "meta": {}}
    text_findings = text_result.get("findings", []) if isinstance(text_result, dict) else []
    visual_findings = _classify_text(text)

    # Ensure both are lists before concatenating
    if not isinstance(text_findings, list):
        text_findings = []
    combined = visual_findings + text_findings

    return {
        "findings": combined,
        "meta": {
            "ocr_engine": ocr.get("engine"),
            "ocr_confidence": ocr.get("confidence"),
            "extracted_text": text[:2000],
            "word_count": ocr.get("word_count", 0),
            "visual_type": _visual_type(visual_findings),
        },
    }


def _visual_type(visual_findings: list[dict]) -> str:
    if not visual_findings:
        return "generic"
    first = visual_findings[0]
    mapping = {
        "login_form": "fake_login_page",
        "payment_request": "fake_payment_request",
        "requests_otp": "otp_phishing",
        "bank_impersonation": "bank_screenshot",
    }
    return mapping.get(first["code"], "generic")
