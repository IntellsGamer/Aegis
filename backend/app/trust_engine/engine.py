"""Model-free, evidence-fusion Digital Trust Score engine.

AEGIS deliberately does not learn from user scans or depend on an LLM.  It turns
observable indicators into a calibrated risk estimate while keeping every
contribution inspectable.  The scorer differs from a flat rule sum in four
important ways:

* it preserves source confidence, evidence multiplicity, and provenance;
* it groups correlated signals so repeated keyword hits cannot dominate a verdict;
* it rewards agreement between independent evidence families (for example, an
  email-authentication failure plus a credential request plus a hostile link);
* it separates risk likelihood from assessment confidence.  A clean scan with
  little observable evidence is therefore *not* presented as a guarantee of safety.
"""
from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Rule
from app.trust_engine.defaults import DEFAULT_EXPLAIN, DEFAULT_RULES, SEVERITY_LEVELS

ENGINE_VERSION = "evidence-fusion-v2"
BASE_RISK_PRIOR = 0.08
MIN_PROBABILITY = 0.001
MAX_PROBABILITY = 0.999

# A stronger observation is represented by a larger likelihood contribution.
# Default rule impacts stay editable in the database; these factors merely map
# their familiar -60..+10 scale into evidence space.
NEGATIVE_IMPACT_SCALE = 10.0
POSITIVE_IMPACT_SCALE = 18.0


@dataclass
class Reason:
    code: str
    title: str
    explanation: str
    evidence: str | None = None
    impact: float = 0.0
    severity: str = "info"
    category: str = "analysis"
    confidence: float = 0.5
    source: str = "heuristic"
    occurrences: int = 1


@dataclass
class EngineResult:
    trust_score: float
    risk_level: str
    confidence: float
    risk_probability: float
    coverage: float
    engine_version: str = ENGINE_VERSION
    reasons: list[Reason] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    highlights: list[str] = field(default_factory=list)
    breakdown: list[dict] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "trust_score": round(self.trust_score, 1),
            "risk_level": self.risk_level,
            "confidence": round(self.confidence, 2),
            "risk_probability": round(self.risk_probability, 4),
            "coverage": round(self.coverage, 3),
            "engine_version": self.engine_version,
            "reasons": [
                {
                    "code": r.code,
                    "title": r.title,
                    "explanation": r.explanation,
                    "evidence": r.evidence,
                    "impact": r.impact,
                    "severity": r.severity,
                    "category": r.category,
                    "confidence": r.confidence,
                    "source": r.source,
                    "occurrences": r.occurrences,
                }
                for r in self.reasons
            ],
            "recommendations": self.recommendations,
            "highlights": self.highlights,
            "breakdown": self.breakdown,
        }


def risk_level_for(trust_score: float) -> str:
    """Compatibility helper for callers that only have a legacy trust score."""
    if trust_score >= 85:
        return "low"
    if trust_score >= 60:
        return "medium"
    if trust_score >= 30:
        return "high"
    return "critical"


def risk_from_score(trust_score: float) -> str:
    return risk_level_for(trust_score)


def _risk_level_for_probability(probability: float) -> str:
    if probability >= 0.95:
        return "critical"
    if probability >= 0.65:
        return "high"
    if probability >= 0.25:
        return "medium"
    return "low"


def _load_rules(db: Session | None) -> dict[str, Rule | dict]:
    """Load enabled rules as code -> rule, using defaults for omitted entries."""
    rules: dict[str, Rule | dict] = {}
    if db is not None:
        try:
            rows = db.scalars(select(Rule).where(Rule.enabled.is_(True))).all()
            rules = {rule.code: rule for rule in rows}
        except Exception:
            # A scan must still complete when an optional rules datastore is unavailable.
            rules = {}
    merged = {item["code"]: item for item in DEFAULT_RULES}
    merged.update(rules)
    return merged


def _value(rule: Rule | dict | None, name: str, fallback: Any = None) -> Any:
    if rule is None:
        return fallback
    if isinstance(rule, Rule):
        return getattr(rule, name, fallback)
    return rule.get(name, fallback)


def _impact_for(rule: Rule | dict | None, finding: dict) -> float:
    if rule is not None:
        return float(_value(rule, "impact", 0.0)) * float(_value(rule, "weight", 1.0))
    return float(finding.get("impact") or 0.0)


def _explain_for(rule: Rule | dict | None, fallback: str | None) -> str:
    return _value(rule, "explain", None) or fallback or DEFAULT_EXPLAIN


def _severity_for(rule: Rule | dict | None, fallback: str) -> str:
    return str(_value(rule, "severity", fallback) or fallback)


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _logit(probability: float) -> float:
    probability = _clamp(probability, MIN_PROBABILITY, MAX_PROBABILITY)
    return math.log(probability / (1.0 - probability))


def _sigmoid(value: float) -> float:
    if value >= 0:
        return 1.0 / (1.0 + math.exp(-value))
    exp_value = math.exp(value)
    return exp_value / (1.0 + exp_value)


def _occurrences(finding: dict) -> int:
    extra = finding.get("extra") or {}
    raw = extra.get("match_count", extra.get("occurrences", 1))
    try:
        return max(1, min(int(raw), 50))
    except (TypeError, ValueError):
        return 1


def _source_for(finding: dict) -> str:
    extra = finding.get("extra") or {}
    source = str(extra.get("source") or "").strip().lower()
    if source:
        return source
    category = str(finding.get("category") or "").lower()
    if category == "email_auth":
        return "email_authentication"
    if category in {"transport", "reputation", "obfuscation", "url_lexical"}:
        return "url_observation"
    if category in {"code", "credential"}:
        return "page_or_request"
    if category in {"manipulation", "fraud", "impersonation"}:
        return "content_semantics"
    return "heuristic"


def _reliability_for(finding: dict) -> float:
    """Estimate how much to trust an observation, not whether it is malicious."""
    try:
        detector_confidence = float(finding.get("confidence", 0.6))
    except (TypeError, ValueError):
        detector_confidence = 0.6
    detector_confidence = _clamp(detector_confidence, 0.15, 0.99)

    source = _source_for(finding)
    source_quality = {
        "known_threat_feed": 0.99,
        "email_authentication": 0.98,
        "tls_observation": 0.94,
        "url_observation": 0.86,
        "page_analysis": 0.82,
        "page_or_request": 0.78,
        "content_semantics": 0.70,
        "pattern": 0.68,
        "heuristic": 0.62,
    }.get(source, 0.62)

    evidence = finding.get("evidence")
    evidence_bonus = 1.0 if evidence else 0.88
    return _clamp(detector_confidence * source_quality * evidence_bonus / 0.75, 0.12, 0.99)


def _channel_for(finding: dict, code: str) -> str:
    """Map correlated indicators to one evidence family for diminishing returns."""
    category = str(finding.get("category") or "analysis").lower()
    if code == "known_threat":
        return "threat_intelligence"
    if code in {"typosquatting", "brand_impersonation", "punycode", "favicon_mismatch"}:
        return "identity"
    if code in {"phishing_link", "shortened_url", "ip_address_url", "url_entropy_high", "open_redirect", "hidden_redirect"}:
        return "link_delivery"
    if category == "email_auth":
        return "email_authentication"
    if category in {"credential", "fraud"}:
        return "requested_action"
    if category == "manipulation":
        return "social_engineering"
    if category in {"transport", "reputation"}:
        return "site_reputation"
    if category in {"code", "obfuscation"}:
        return "page_behavior"
    return category


def _evidence_mass(impact: float, reliability: float, occurrences: int) -> float:
    """Convert a tunable rule impact to a likelihood contribution.

    Repetition is intentionally sub-linear: a message containing the same cue
    ten times is not ten independent observations.
    """
    if impact == 0:
        return 0.0
    density = 1.0 + min(0.35, math.log1p(max(occurrences - 1, 0)) / 4.0)
    scale = NEGATIVE_IMPACT_SCALE if impact < 0 else POSITIVE_IMPACT_SCALE
    return (abs(impact) / scale) * reliability * density * (1.0 if impact < 0 else -1.0)


def _fuse_channel(masses: Iterable[float]) -> float:
    """Fuse one evidence family with diminishing returns for correlated signals."""
    positive = sorted((mass for mass in masses if mass > 0), reverse=True)
    negative = sorted((-mass for mass in masses if mass < 0), reverse=True)

    def diminishing(values: list[float]) -> float:
        return sum(value * (0.62 ** index) for index, value in enumerate(values))

    # Positive mass increases risk, negative mass decreases it.
    return _clamp(diminishing(positive) - diminishing(negative), -3.0, 4.5)


def _interaction_bonus(channel_masses: dict[str, float], codes: set[str]) -> float:
    """Reward agreement from independent attack stages, never duplicate wording."""
    bonus = 0.0
    hostile_link = channel_masses.get("link_delivery", 0.0) > 0.8
    identity = channel_masses.get("identity", 0.0) > 0.8
    requested_action = channel_masses.get("requested_action", 0.0) > 0.7
    email_failure = channel_masses.get("email_authentication", 0.0) > 0.8
    social_pressure = channel_masses.get("social_engineering", 0.0) > 0.8

    if hostile_link and (identity or requested_action):
        bonus += 0.90
    if email_failure and (requested_action or hostile_link or identity):
        bonus += 0.85
    if social_pressure and requested_action:
        bonus += 0.45
    if "known_threat" in codes:
        # A verified local threat-intelligence match is an independent, direct
        # observation; do not let benign transport indicators cancel it.
        bonus += 1.15
    return min(bonus, 2.5)


_BASE_RECOMMENDATIONS = {
    "low": [
        "No high-risk evidence was observed. This is not proof of safety; verify the sender or destination independently before sharing sensitive information.",
        "Use a password manager and multi-factor authentication for important accounts.",
    ],
    "medium": [
        "Treat this as unverified. Do not use message-provided links, phone numbers, or contact details to validate it.",
        "Verify the request through a known official website, app, or an independent contact channel.",
    ],
    "high": [
        "Do not click links, open attachments, reply, or provide credentials or payment information.",
        "Verify the claimed organization independently and report the message or site through its official channel.",
        "If information was already shared, change affected credentials and contact the real service immediately.",
    ],
    "critical": [
        "Stop interacting with this content. It has multiple independent signs of a likely scam or a verified threat match.",
        "Block and report the sender or URL. If financial or account data was shared, contact the legitimate provider immediately.",
        "Change exposed passwords and revoke active sessions from a trusted device.",
    ],
}


def compute_trust_score(
    findings: list[dict],
    db: Session | None = None,
    ai_confidence: float | None = None,
    ai_label: str | None = None,
) -> EngineResult:
    """Produce an explainable score from deterministic, observable evidence.

    ``ai_confidence`` and ``ai_label`` are accepted only for backwards API
    compatibility and deliberately ignored.  AEGIS v2 neither trains nor uses a
    statistical text model during prediction.
    """
    del ai_confidence, ai_label
    rules = _load_rules(db)

    # Keep the strongest duplicate observation per code.  Scanner stages can
    # rediscover the same indicator; treating them as independent is a common
    # cause of artificially dramatic scores.
    grouped: dict[str, list[dict]] = defaultdict(list)
    for finding in findings:
        code = str(finding.get("code") or "").strip()
        if code:
            grouped[code].append(finding)

    reasons: list[Reason] = []
    channel_evidence: dict[str, list[float]] = defaultdict(list)
    channel_reliability: dict[str, list[float]] = defaultdict(list)
    observed_codes: set[str] = set()

    for code, duplicates in grouped.items():
        rule = rules.get(code)
        # For a hostile code, preserve the strongest negative contribution. For
        # a positive code, preserve the strongest positive contribution.
        candidates = []
        for finding in duplicates:
            impact = _impact_for(rule, finding)
            reliability = _reliability_for(finding)
            occurrences = _occurrences(finding)
            mass = _evidence_mass(impact, reliability, occurrences)
            candidates.append((mass, impact, reliability, occurrences, finding))
        selected = max(candidates, key=lambda item: abs(item[0]))
        mass, impact, reliability, occurrences, finding = selected
        observed_codes.add(code)

        severity = _severity_for(rule, str(finding.get("severity") or "info"))
        channel = _channel_for(finding, code)
        channel_evidence[channel].append(mass)
        channel_reliability[channel].append(reliability)
        source = _source_for(finding)
        title = str(finding.get("title") or _value(rule, "name", None) or code)

        # Impacts in the UI are calibrated contributions, not a misleading
        # unweighted rule table value.
        display_impact = -round(abs(mass) * 10.0, 2) if mass > 0 else round(abs(mass) * 10.0, 2)
        reasons.append(
            Reason(
                code=code,
                title=title,
                explanation=_explain_for(rule, finding.get("description")),
                evidence=finding.get("evidence"),
                impact=display_impact,
                severity=severity,
                category=str(finding.get("category") or _value(rule, "category", "analysis")),
                confidence=round(reliability, 3),
                source=source,
                occurrences=sum(_occurrences(item) for item in duplicates),
            )
        )

    channel_masses = {
        channel: _fuse_channel(masses) for channel, masses in channel_evidence.items()
    }
    log_odds = _logit(BASE_RISK_PRIOR) + sum(channel_masses.values())
    log_odds += _interaction_bonus(channel_masses, observed_codes)
    risk_probability = _clamp(_sigmoid(log_odds), MIN_PROBABILITY, MAX_PROBABILITY)
    if "known_threat" in observed_codes:
        # A local, curated threat-intelligence match is direct evidence. General
        # safety indicators such as TLS cannot turn a known hostile destination
        # into a merely high-risk verdict.
        risk_probability = max(risk_probability, 0.97)
    trust_score = (1.0 - risk_probability) * 100.0
    risk_level = _risk_level_for_probability(risk_probability)

    # Confidence measures observability and source diversity, not how strongly
    # the engine feels about a verdict.  This prevents an empty scan from being
    # presented as confidently benign.
    reliability_total = sum(sum(values) for values in channel_reliability.values())
    coverage = 1.0 - math.exp(-reliability_total / 3.2)
    diversity = min(len(channel_masses) / 4.0, 1.0)
    margin = min(abs(risk_probability - 0.5) * 2.0, 1.0)
    confidence = 0.16 + 0.34 * coverage + 0.25 * diversity + 0.20 * margin
    if not reasons:
        confidence = min(confidence, 0.38)
    confidence = _clamp(confidence, 0.05, 0.98)

    recommendations = list(_BASE_RECOMMENDATIONS[risk_level])
    for reason in sorted(reasons, key=lambda item: item.impact)[:3]:
        if reason.impact < 0 and reason.evidence:
            recommendations.append(f"Evidence to verify: {reason.title} — {reason.evidence[:180]}")

    highlights = [
        reason.title for reason in sorted(reasons, key=lambda item: item.impact) if reason.impact < 0
    ][:6]
    if not highlights:
        highlights = ["No high-risk evidence observed", "Assessment confidence is limited by available evidence"]

    breakdown = [
        {
            "category": channel,
            "impact": round(mass, 3),
            "evidence_count": len(channel_evidence[channel]),
            "reliability": round(sum(channel_reliability[channel]) / len(channel_reliability[channel]), 3),
        }
        for channel, mass in sorted(channel_masses.items(), key=lambda item: abs(item[1]), reverse=True)
    ]

    return EngineResult(
        trust_score=round(trust_score, 1),
        risk_level=risk_level,
        confidence=round(confidence, 3),
        risk_probability=round(risk_probability, 4),
        coverage=round(coverage, 3),
        reasons=reasons,
        recommendations=recommendations[:10],
        highlights=highlights,
        breakdown=breakdown,
    )


def severity_rank(severity: str) -> int:
    return SEVERITY_LEVELS.get(severity, 0)
