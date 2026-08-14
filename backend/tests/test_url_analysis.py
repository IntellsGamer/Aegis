"""Precision regressions for local URL lexical analysis."""
from __future__ import annotations

from app.ai.url_analysis import detect_typosquatting


def test_typosquatting_uses_domain_label_not_whole_hostname_noise():
    brand, score = detect_typosquatting("example.com")
    assert brand is None
    assert score == 0.0


def test_typosquatting_detects_mutated_brand_token():
    brand, score = detect_typosquatting("paypa1-login.example")
    assert brand == "paypal"
    assert score >= 0.82


def test_typosquatting_detects_compound_brand_label_but_not_legitimate_subdomain():
    assert detect_typosquatting("paypal-security.example")[0] == "paypal"
    assert detect_typosquatting("login.paypal.com")[0] is None
