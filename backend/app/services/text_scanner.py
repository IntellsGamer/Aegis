"""Text scanner: pattern analysis + ML classifier for SMS/chat/ads/emails."""
from __future__ import annotations

import asyncio

from app.ai.features import build_text_feature_row
from app.ai.model_manager import model_manager
from app.ai.text_patterns import (
    IP_ADDR_RE,
    URL_RE,
    scan_patterns,
)
from app.config import settings


async def scan_text(text: str) -> dict:
    return await asyncio.to_thread(_scan_text_sync, text)


def _scan_text_sync(text: str) -> dict:
    findings, signal_count = scan_patterns(text)

    # --- embedded URLs ------------------------------------------------------
    urls = URL_RE.findall(text)
    for url in urls[:5]:
        lower = url.lower()
        suspicious = (
            any(h in lower for h in ("bit.ly", "tinyurl", "shorturl", "goo.gl", "t.co", "cutt.ly", "rb.gy"))
            or "://" in lower
            and bool(IP_ADDR_RE.search(url))
        )
        if suspicious:
            findings.append({
                "code": "phishing_link",
                "category": "impersonation",
                "title": "Phishing link detected",
                "description": "The message contains a link that looks suspicious.",
                "evidence": url[:250],
                "severity": "critical",
                "impact": 0.0,
                "confidence": 0.8,
            })
            break

    # --- ML classifier ------------------------------------------------------
    ai_label = None
    ai_probability = None
    if settings.ai_enabled and text.strip():
        try:
            label, prob, scam_prob = model_manager.predict_text(text)
            if model_manager.text_model.pipeline is not None:
                ai_label = "scam" if label == 1 else "legitimate"
                ai_probability = round(prob, 3)
                findings.append({
                    "code": "ml_scam_probability",
                    "category": "ml",
                    "title": "AI classification",
                    "description": (
                        f"The AI model classifies this message as {ai_label} "
                        f"with {scam_prob:.0%} scam probability."
                    ),
                    "evidence": None,
                    "severity": "high" if scam_prob >= 0.6 else "safe",
                    "impact": -12.0 if scam_prob >= 0.6 else 2.0,
                    "confidence": round(prob, 2),
                    "extra": {"scam_probability": round(scam_prob, 3)},
                })
        except Exception:
            pass

    # --- positive fallback ---------------------------------------------------
    if not any(f["code"] == "no_scam_patterns" for f in findings) and signal_count == 0:
        findings.append({
            "code": "no_scam_patterns",
            "category": "analysis",
            "title": "No scam patterns found",
            "description": "No known scam indicators were found in the content.",
            "evidence": None,
            "severity": "safe",
            "impact": 0.0,
            "confidence": 0.65,
        })

    return {
        "findings": findings,
        "meta": {
            "char_count": len(text),
            "url_count": len(urls),
            "signal_count": signal_count,
            "ai_label": ai_label,
            "ai_probability": ai_probability,
        },
    }
