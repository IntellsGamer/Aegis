"""Text scanner using deterministic linguistic and link evidence only."""
from __future__ import annotations

import asyncio

from app.ai.link_analysis import analyze_embedded_url
from app.ai.text_patterns import URL_RE, scan_patterns


async def scan_text(text: str) -> dict:
    return await asyncio.to_thread(_scan_text_sync, text)


def _scan_text_sync(text: str) -> dict:
    findings, signal_count = scan_patterns(text)
    urls = URL_RE.findall(text)
    link_assessments: list[dict] = []
    link_findings: list[dict] = []

    # A link is analyzed locally rather than fetched here. This gives a text
    # scan strong URL evidence without exposing it to network instability or
    # making a second opaque prediction.
    for url in urls[:5]:
        url_findings, assessment = analyze_embedded_url(url)
        link_findings.extend(url_findings)
        link_assessments.append({"url": url[:500], **assessment})

    if link_findings:
        # A message containing a suspicious link is not entitled to the
        # pattern-only clean fallback, even when its prose has no scam phrases.
        findings = [item for item in findings if item.get("code") != "no_scam_patterns"]
        findings.extend(link_findings)

    if not findings and signal_count == 0:
        findings.append({
            "code": "no_scam_patterns",
            "category": "analysis",
            "title": "No high-risk patterns observed",
            "description": "No deterministic high-risk patterns were observed in the provided text.",
            "evidence": None,
            "severity": "safe",
            "impact": 0.0,
            "confidence": 0.45,
            "extra": {"source": "pattern", "match_count": 0},
        })

    return {
        "findings": findings,
        "meta": {
            "char_count": len(text),
            "url_count": len(urls),
            "signal_count": signal_count,
            "link_assessments": link_assessments,
            "predictor": "deterministic-evidence-fusion",
        },
    }
