"""Regression tests for the deterministic Evidence Fusion predictor."""
from __future__ import annotations

from app.services.text_scanner import _scan_text_sync
from app.trust_engine.engine import compute_trust_score


def _assess(text: str):
    raw = _scan_text_sync(text)
    return compute_trust_score(raw["findings"]), raw


def test_independent_phishing_evidence_reaches_critical_risk():
    result, raw = _assess(
        "URGENT: your bank account will be locked. Click "
        "http://paypa1-login.example/verify immediately and enter your password."
    )

    assert result.risk_level == "critical"
    assert result.risk_probability >= 0.95
    assert result.confidence >= 0.70
    assert raw["meta"]["predictor"] == "deterministic-evidence-fusion"
    assert {item["code"] for item in raw["findings"]} >= {
        "urgency_words", "typosquatting", "suspicious_keywords_url"
    }


def test_benign_topical_content_is_not_a_bank_impersonation():
    result, raw = _assess(
        "This security article explains how financial institutions protect customers "
        "from fraud and why independently verifying a sender matters."
    )

    assert result.risk_level == "low"
    assert result.risk_probability < 0.25
    assert "bank_impersonation" not in {item["code"] for item in raw["findings"]}


def test_repeated_cue_has_bounded_effect_without_independent_evidence():
    one = compute_trust_score([
        {"code": "urgency_words", "category": "manipulation", "confidence": 0.8,
         "evidence": "urgent", "extra": {"source": "pattern", "match_count": 1}},
    ])
    repeated = compute_trust_score([
        {"code": "urgency_words", "category": "manipulation", "confidence": 0.8,
         "evidence": "urgent", "extra": {"source": "pattern", "match_count": 20}},
    ])

    assert repeated.risk_probability > one.risk_probability
    assert repeated.risk_probability < 0.50
    assert repeated.risk_level in {"low", "medium"}


def test_verified_threat_is_not_cancelled_by_benign_transport_observations():
    result = compute_trust_score([
        {"code": "known_threat", "category": "reputation", "confidence": 0.99,
         "evidence": "https://evil.example", "extra": {"source": "known_threat_feed"}},
        {"code": "https_secure", "category": "transport", "confidence": 0.95,
         "evidence": "TLS", "extra": {"source": "tls_observation"}},
        {"code": "domain_very_old", "category": "reputation", "confidence": 0.8,
         "evidence": "3000 days", "extra": {"source": "url_observation"}},
    ])

    assert result.risk_level == "critical"
    assert result.risk_probability >= 0.95
    assert result.trust_score <= 5.0


def test_empty_evidence_does_not_produce_overconfident_safety():
    result = compute_trust_score([])

    assert result.risk_level == "low"
    assert result.confidence <= 0.38
    assert result.coverage == 0.0


def test_text_scan_keeps_local_link_evidence_without_model_inference():
    result, raw = _assess("Please review https://bit.ly/claim-your-prize today.")

    assert raw["meta"]["link_assessments"]
    assert "shortened_url" in {item["code"] for item in raw["findings"]}
    assert result.risk_level in {"medium", "high", "critical"}
