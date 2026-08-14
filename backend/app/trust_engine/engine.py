"""The explainable Digital Trust Score engine.

Design
------
- A scan produces a list of findings (indicators). Each finding has a `code`.
- The engine maps each code to a configurable rule (impact + weight) fetched
  from the database (with a built-in default registry as fallback).
- The score starts at a neutral 50, then each applicable rule shifts it.
- The engine always emits human-readable reasons and recommendations so the
  result is fully explainable.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Rule
from app.trust_engine.defaults import (
    DEFAULT_EXPLAIN,
    DEFAULT_RULES,
    SEVERITY_LEVELS,
)

BASE_SCORE = 50.0
MIN_SCORE = 0.0
MAX_SCORE = 100.0


def risk_level_for(trust_score: float) -> str:
    if trust_score >= 75:
        return "low"
    if trust_score >= 50:
        return "medium"
    if trust_score >= 25:
        return "high"
    return "critical"


def risk_from_score(trust_score: float) -> str:
    return risk_level_for(trust_score)


@dataclass
class Reason:
    code: str
    title: str
    explanation: str
    evidence: str | None = None
    impact: float = 0.0
    severity: str = "info"
    category: str = "analysis"


@dataclass
class EngineResult:
    trust_score: float
    risk_level: str
    confidence: float
    reasons: list[Reason] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    highlights: list[str] = field(default_factory=list)
    breakdown: list[dict] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "trust_score": round(self.trust_score, 1),
            "risk_level": self.risk_level,
            "confidence": round(self.confidence, 2),
            "reasons": [
                {
                    "code": r.code,
                    "title": r.title,
                    "explanation": r.explanation,
                    "evidence": r.evidence,
                    "impact": r.impact,
                    "severity": r.severity,
                    "category": r.category,
                }
                for r in self.reasons
            ],
            "recommendations": self.recommendations,
            "highlights": self.highlights,
            "breakdown": self.breakdown,
        }


def _load_rules(db: Session | None) -> dict[str, Rule | dict]:
    """Load enabled rules as code -> (impact, weight, explain, severity)."""
    rules: dict[str, Rule | dict] = {}
    if db is not None:
        try:
            rows = db.scalars(select(Rule).where(Rule.enabled.is_(True))).all()
            for rule in rows:
                rules[rule.code] = rule
        except Exception:
            rules = {}
    defaults = {d["code"]: d for d in DEFAULT_RULES}
    # DB overrides defaults; missing defaults are added.
    merged = dict(defaults)
    merged.update(rules)
    return merged


def _explain_for(rule: Rule | dict, fallback: str | None) -> str:
    text = getattr(rule, "explain", None) if isinstance(rule, Rule) else rule.get("explain")
    if not text:
        text = fallback or DEFAULT_EXPLAIN
    return text


def _impact_for(rule: Rule | dict) -> float:
    if isinstance(rule, Rule):
        return float(rule.impact) * float(rule.weight)
    return float(rule.get("impact", 0.0)) * float(rule.get("weight", 1.0))


def _severity_for(rule: Rule | dict, fallback: str) -> str:
    if isinstance(rule, Rule):
        return rule.severity or fallback
    return rule.get("severity", fallback)


# --- Recommendations per risk level, appended with evidence-based ones ---
_BASE_RECOMMENDATIONS = {
    "low": [
        "The content looks generally safe, but always stay alert and verify "
        "the sender independently.",
        "Do not reuse passwords; enable two-factor authentication on your "
        "important accounts.",
    ],
    "medium": [
        "This content shows some risk indicators. Do not click links or "
        "download attachments until you verify the sender by another channel.",
        "If the message asks for personal data, contact the organization "
        "directly using an official phone number or website.",
    ],
    "high": [
        "Do NOT click any links, open attachments, or reply to this message.",
        "The content shows strong signs of a scam. Report it to your bank or "
        "local cyber-security authorities.",
        "If you already shared information, change your passwords and enable "
        "two-factor authentication immediately.",
    ],
    "critical": [
        "STOP. This content is very likely a scam. Do not respond, click, or "
        "share any information.",
        "Block and report the sender. Notify your bank if financial details "
        "were shared.",
        "If you already entered a password or code, change it right now and "
        "contact the real organization.",
    ],
}


def compute_trust_score(
    findings: list[dict],
    db: Session | None = None,
    ai_confidence: float | None = None,
    ai_label: str | None = None,
) -> EngineResult:
    """Score a list of findings into an explainable EngineResult.

    `findings` is a list of dicts with at least `code`; other useful keys are
    `title`, `description`, `evidence`, `severity`, `impact`, `category`.
    """
    rules = _load_rules(db)
    score = BASE_SCORE
    reasons: list[Reason] = []
    seen: set[str] = set()

    for finding in findings:
        code = finding.get("code")
        if not code:
            continue
        rule = rules.get(code)
        impact = _impact_for(rule) if rule else float(finding.get("impact") or 0.0)
        severity = (
            _severity_for(rule, finding.get("severity", "info"))
            if rule
            else finding.get("severity", "info")
        )
        # A finding may re-fire; only count the strongest impact once.
        if code in seen:
            continue
        seen.add(code)
        score += impact
        explanation = _explain_for(rule, finding.get("description"))
        title = finding.get("title") or (getattr(rule, "name", None) if isinstance(rule, Rule) else rule.get("name")) or code
        reasons.append(
            Reason(
                code=code,
                title=title,
                explanation=explanation,
                evidence=finding.get("evidence"),
                impact=round(impact, 2),
                severity=severity,
                category=finding.get("category", "analysis"),
            )
        )

    score = max(MIN_SCORE, min(MAX_SCORE, score))

    # Confidence: based on signal volume + optional AI agreement.
    n_signal = len([r for r in reasons if r.impact != 0])
    volume_conf = 1.0 - math.exp(-n_signal / 4.0)
    confidence = 0.45 + 0.3 * volume_conf
    if ai_confidence is not None:
        ai_agreement = 1.0 - abs(0.5 - ai_confidence) * 2
        confidence = confidence * 0.6 + ai_agreement * 0.4
    # Neutral scans (no signals) have modest confidence.
    if n_signal == 0:
        confidence = min(confidence, 0.55)
    confidence = max(0.0, min(0.99, confidence))

    risk_level = risk_level_for(score)

    recommendations = list(_BASE_RECOMMENDATIONS[risk_level])
    for reason in sorted(reasons, key=lambda r: r.impact):
        if reason.impact < 0 and reason.evidence:
            recommendations.append(
                f"Specific warning: {reason.title} - {reason.evidence[:180]}"
            )
            if len(recommendations) > 10:
                break

    highlights = []
    for reason in sorted(reasons, key=lambda r: r.impact)[:6]:
        if reason.impact < 0:
            highlights.append(reason.title)
    if score >= 75:
        highlights.insert(0, "No significant threats detected")

    breakdown = [
        {
            "category": reason.category,
            "title": reason.title,
            "impact": reason.impact,
            "severity": reason.severity,
            "count": 1,
        }
        for reason in reasons
    ]

    return EngineResult(
        trust_score=round(score, 1),
        risk_level=risk_level,
        confidence=round(confidence, 3),
        reasons=reasons,
        recommendations=recommendations[:12],
        highlights=highlights[:8],
        breakdown=breakdown,
    )


def severity_rank(severity: str) -> int:
    return SEVERITY_LEVELS.get(severity, 0)
