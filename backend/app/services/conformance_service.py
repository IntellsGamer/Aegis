"""Deterministic conformance checks for the production assessment pipeline.

This is intentionally not a detection benchmark.  Fixtures are fictional and
versioned in code so maintainers can catch regressions in declared engine
contracts without presenting the result as real-world accuracy.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.services.text_scanner import _scan_text_sync
from app.trust_engine.engine import ENGINE_VERSION, compute_trust_score

SUITE_VERSION = "conformance-2026.1"

_FIXTURES = (
    {
        "id": "benign-baseline",
        "title": "Ordinary service notice remains low risk",
        "description": "A plain fictional event reminder should not be converted into a high-risk verdict.",
        "input": "The fictional community library closes at 17:00 today. Visit https://library.example.org/hours for opening times.",
        "expect": {"risk_in": {"low"}, "codes_absent": {"typosquatting", "urgency", "phishing_link"}},
    },
    {
        "id": "credential-lure",
        "title": "Brand-like credential lure produces multiple observable cues",
        "description": "A fictional credential lure must retain its lookalike, urgency, and link evidence.",
        "input": "Urgent: verify your account now at https://paypa1-account-review.example/verify?account=demo. This is a fictional test fixture.",
        "expect": {"risk_in": {"high", "critical"}, "codes_present": {"typosquatting", "suspicious_keywords_url", "urgency_words"}},
    },
    {
        "id": "obscured-link",
        "title": "Obscured sensitive-action links remain explainable",
        "description": "A fictional shortened credential link should identify both shortening and the sensitive action.",
        "input": "Fictional test: confirm payment details at https://bit.ly/verify-account-demo.",
        "expect": {"risk_in": {"medium", "high", "critical"}, "codes_present": {"shortened_url", "suspicious_keywords_url", "phishing_link"}},
    },
)


def _run_fixture(fixture: dict, db: Session | None = None) -> dict:
    scan = _scan_text_sync(fixture["input"])
    result = compute_trust_score(scan["findings"], db=db)
    codes = {reason.code for reason in result.reasons}
    expect = fixture["expect"]
    checks = []

    expected_risks = set(expect.get("risk_in", set()))
    if expected_risks:
        checks.append({
            "name": f"Risk level is one of {', '.join(sorted(expected_risks))}",
            "passed": result.risk_level in expected_risks,
            "observed": result.risk_level,
        })
    for code in sorted(expect.get("codes_present", set())):
        checks.append({"name": f"Retains {code}", "passed": code in codes, "observed": code if code in codes else "missing"})
    for code in sorted(expect.get("codes_absent", set())):
        checks.append({"name": f"Does not invent {code}", "passed": code not in codes, "observed": "absent" if code not in codes else "present"})

    passed = all(check["passed"] for check in checks)
    return {
        "id": fixture["id"], "title": fixture["title"], "description": fixture["description"],
        "passed": passed, "checks": checks,
        "observed": {
            "risk_level": result.risk_level,
            "trust_score": round(result.trust_score, 1),
            "confidence": round(result.confidence, 2),
            "finding_codes": sorted(codes),
            "evidence_families": [item["category"] for item in result.breakdown],
        },
    }


def run_conformance_suite(db: Session | None = None) -> dict:
    """Run fixed fictional cases against the active production parser and scorer."""
    cases = [_run_fixture(fixture, db) for fixture in _FIXTURES]
    passed = sum(case["passed"] for case in cases)
    return {
        "suite_version": SUITE_VERSION,
        "engine_version": ENGINE_VERSION,
        "kind": "deterministic conformance",
        "purpose": "Regression checks for declared behavior; not a benchmark or a measured accuracy claim.",
        "fixtures_notice": "All fixtures are fictional, static, and executed locally without live threat acquisition.",
        "summary": {"total": len(cases), "passed": passed, "failed": len(cases) - passed},
        "cases": cases,
    }
