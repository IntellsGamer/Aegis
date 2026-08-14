"""Feature extraction for text and URL classification."""
from __future__ import annotations

import re

from app.ai.text_patterns import (
    IP_ADDR_RE,
    SHORTENER_HOSTS,
    WORD_RE,
    find_matches,
    match_count,
    _BANK_PATTERNS,
    _CRYPTO_PATTERNS,
    _FAKE_JOB_PATTERNS,
    _FEAR_PATTERNS,
    _GOV_PATTERNS,
    _IDENTITY_PATTERNS,
    _INVESTMENT_PATTERNS,
    _LOTTERY_PATTERNS,
    _MONEY_PATTERNS,
    _OTP_PATTERNS,
    _PASSWORD_PATTERNS,
    _REMOTE_PATTERNS,
    _REWARD_PATTERNS,
    _ROMANCE_PATTERNS,
    _SOCIAL_PATTERNS,
    _URGENCY_PATTERNS,
    _VERIFICATION_PATTERNS,
)
from app.ai.url_analysis import extract_url_features

URL_IN_TEXT_RE = re.compile(r"https?://[^\s<>'\"\]]+", re.IGNORECASE)

_TEXT_FEATURE_KEYS = [
    "len", "words", "sentences", "caps_ratio", "exclamations",
    "digits_ratio", "urls", "shortened_urls", "ip_addresses",
    "urgency", "fear", "reward", "lottery", "investment", "crypto",
    "fake_job", "romance", "government", "bank", "otp", "password",
    "verification", "identity", "remote", "social", "money",
]


def text_features(text: str) -> dict:
    """Hand-crafted features used by the ML classifier."""
    words = WORD_RE.findall(text.lower())
    total = max(len(words), 1)
    sentences = max(len([s for s in re.split(r"[.!?]+", text) if s.strip()]), 1)
    caps_ratio = sum(1 for w in words if w.isupper()) / total
    digits = sum(1 for ch in text if ch.isdigit())
    urls = URL_IN_TEXT_RE.findall(text)
    shortened = sum(1 for u in urls if any(h in u for h in SHORTENER_HOSTS))
    ips = len(IP_ADDR_RE.findall(text))

    feature_sets = [
        ("urgency", _URGENCY_PATTERNS), ("fear", _FEAR_PATTERNS),
        ("reward", _REWARD_PATTERNS), ("lottery", _LOTTERY_PATTERNS),
        ("investment", _INVESTMENT_PATTERNS), ("crypto", _CRYPTO_PATTERNS),
        ("fake_job", _FAKE_JOB_PATTERNS), ("romance", _ROMANCE_PATTERNS),
        ("government", _GOV_PATTERNS), ("bank", _BANK_PATTERNS),
        ("otp", _OTP_PATTERNS), ("password", _PASSWORD_PATTERNS),
        ("verification", _VERIFICATION_PATTERNS), ("identity", _IDENTITY_PATTERNS),
        ("remote", _REMOTE_PATTERNS), ("social", _SOCIAL_PATTERNS),
        ("money", _MONEY_PATTERNS),
    ]

    features: dict = {
        "len": len(text),
        "words": total,
        "sentences": sentences,
        "caps_ratio": round(caps_ratio, 4),
        "exclamations": text.count("!"),
        "digits_ratio": round(digits / max(len(text), 1), 4),
        "urls": len(urls),
        "shortened_urls": shortened,
        "ip_addresses": ips,
    }
    for name, patterns in feature_sets:
        features[name] = match_count(patterns, text)
    return features


def url_features(url: str) -> dict:
    """Wrapper around the URL analyzer feature vector."""
    return extract_url_features(url)


# Fixed feature ordering for the URL classifier.
URL_FEATURE_KEYS = [
    "url_len", "host_len", "path_len", "num_dots", "num_digits",
    "num_dashes", "num_subdomains", "entropy", "has_ip", "has_port",
    "https", "punycode", "suspicious_tld", "shortener", "typosquat",
    "brand_word", "login_word", "pay_word", "verify_word", "free_word",
    "double_slash", "at_sign", "random_path",
]


def build_text_feature_row(text: str) -> list[float]:
    f = text_features(text)
    return [float(f[k]) for k in _TEXT_FEATURE_KEYS]


def build_url_feature_row(url: str) -> list[float]:
    f = url_features(url)
    return [float(f[k]) for k in URL_FEATURE_KEYS]
