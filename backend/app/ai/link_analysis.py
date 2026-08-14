"""Deterministic lexical analysis for links embedded in text and email.

This module performs no network requests and has no trained component.  It is
safe to use on every extracted link and deliberately reports observable URL
properties rather than pretending to know intent from a single keyword.
"""
from __future__ import annotations

import difflib
import re
from urllib.parse import urlparse

from app.ai.url_analysis import (
    BRANDS,
    PUNYCODE_RE,
    SUSPICIOUS_TLDS,
    contains_suspicious_keywords,
    detect_redirect_url,
    entropy_of,
    extract_tld,
    is_ip_address,
    is_shortened,
)

_LABEL_RE = re.compile(r"[a-z0-9]+", re.IGNORECASE)


def _finding(
    code: str,
    category: str,
    title: str,
    description: str,
    severity: str,
    evidence: str,
    confidence: float,
    **extra: object,
) -> dict:
    return {
        "code": code,
        "category": category,
        "title": title,
        "description": description,
        "severity": severity,
        "evidence": evidence[:500],
        "impact": 0.0,
        "confidence": confidence,
        "extra": {"source": "url_observation", **extra},
    }


def _label_typosquat(host: str) -> tuple[str | None, float]:
    """Find deceptive brand-like labels even when a suffix obscures the host."""
    labels = _LABEL_RE.findall(host.lower())
    for label in labels:
        if len(label) < 4:
            continue
        for brand in BRANDS:
            # An embedded brand in a registrable-looking label is suspicious
            # unless it is simply the real brand label.
            if brand in label and label != brand:
                return brand, 0.95
            if abs(len(label) - len(brand)) <= 2:
                ratio = difflib.SequenceMatcher(None, label, brand).ratio()
                if ratio >= 0.82:
                    return brand, ratio
    return None, 0.0


def analyze_embedded_url(url: str) -> tuple[list[dict], dict]:
    """Return explainable, local-only evidence for a URL extracted from text."""
    candidate = url.strip().rstrip(".,;:!?)\]\}")
    parsed = urlparse(candidate if "://" in candidate else f"https://{candidate}")
    host = (parsed.hostname or "").lower()
    path_and_query = f"{parsed.path}?{parsed.query}"
    findings: list[dict] = []

    if not host:
        return findings, {"host": "", "local_risk": 0.0}

    if is_ip_address(host):
        findings.append(_finding(
            "ip_address_url", "obfuscation", "IP address used as destination",
            "The link uses a numeric IP address instead of a named domain.", "high", host, 0.97,
        ))
    if PUNYCODE_RE.search(host):
        findings.append(_finding(
            "punycode", "impersonation", "Punycode / homograph destination",
            "The hostname uses encoded international characters that can visually imitate another domain.",
            "high", host, 0.93,
        ))
    if "@" in candidate:
        findings.append(_finding(
            "url_entropy_high", "obfuscation", "Misleading @ in URL",
            "An @ symbol can disguise the true destination host in a URL.", "high", candidate, 0.92,
        ))
    if parsed.port and parsed.port not in (80, 443):
        findings.append(_finding(
            "url_entropy_high", "obfuscation", "Non-standard destination port",
            "The link uses a non-standard network port.", "medium", str(parsed.port), 0.75,
        ))

    shortened, short_host = is_shortened(candidate)
    if shortened:
        findings.append(_finding(
            "shortened_url", "obfuscation", "Shortened destination link",
            "The visible link hides its final destination behind a URL shortener.",
            "medium", short_host or host, 0.95,
        ))

    redirect, target = detect_redirect_url(candidate)
    if redirect:
        findings.append(_finding(
            "open_redirect", "obfuscation", "Redirect payload in URL",
            "The link contains a second destination encoded in a redirect parameter.",
            "medium", target or candidate, 0.9,
        ))

    tld = extract_tld(host)
    if tld in SUSPICIOUS_TLDS:
        findings.append(_finding(
            "suspicious_tld", "reputation", "High-abuse top-level domain",
            "The destination uses a top-level domain with elevated abuse exposure.",
            "medium", tld, 0.75,
        ))

    brand, similarity = _label_typosquat(host)
    if brand is None:
        brand, similarity = _fallback_typosquat(host)
    if brand:
        findings.append(_finding(
            "typosquatting", "impersonation", "Brand-like destination hostname",
            f"The destination hostname closely resembles '{brand}' without being the verified brand domain.",
            "critical", host, min(0.98, 0.80 + similarity * 0.18), brand=brand, similarity=round(similarity, 3),
        ))

    keywords = contains_suspicious_keywords(candidate)
    if keywords:
        findings.append(_finding(
            "suspicious_keywords_url", "obfuscation", "Sensitive-action words in link",
            "The URL includes account, credential, payment, or verification terms often used in phishing flows.",
            "medium", ", ".join(keywords[:6]), min(0.9, 0.55 + 0.06 * len(keywords)), keywords=keywords[:10],
        ))
    if shortened and keywords:
        findings.append(_finding(
            "phishing_link", "impersonation", "Obscured sensitive-action link",
            "The link both hides its destination and advertises a credential, payment, or reward action.",
            "high", candidate, 0.9, keywords=keywords[:10],
        ))

    entropy = entropy_of(host + path_and_query)
    if entropy > 4.35:
        findings.append(_finding(
            "url_entropy_high", "obfuscation", "Random-looking URL structure",
            "The hostname or path has unusually high character entropy.", "low", f"entropy={entropy:.2f}", 0.63,
        ))

    # This aggregate is only metadata.  The engine fuses individual signals and
    # does not score an opaque aggregate as a second independent observation.
    local_risk = sum(
        {"critical": 3.0, "high": 2.0, "medium": 1.0, "low": 0.4}.get(item["severity"], 0.0)
        for item in findings
    )
    return findings, {
        "host": host,
        "scheme": parsed.scheme.lower(),
        "local_risk": round(local_risk, 2),
        "entropy": round(entropy, 3),
        "suspicious_feature_count": len(findings),
    }


def _fallback_typosquat(host: str) -> tuple[str | None, float]:
    """Use the shared hostname check after robust label-level checks."""
    from app.ai.url_analysis import detect_typosquatting

    return detect_typosquatting(host)
