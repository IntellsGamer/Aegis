"""Input validators and normalizers used across the API."""
from __future__ import annotations

import re
from urllib.parse import urlparse

URL_RE = re.compile(r"^https?://", re.IGNORECASE)


def is_valid_url(value: str) -> bool:
    """Return True when value looks like an absolute http(s) URL."""
    if not value or len(value) > 2048:
        return False
    if not URL_RE.match(value):
        return False
    parsed = urlparse(value)
    if not parsed.hostname:
        return False
    if any(ch in value for ch in (" ", "\t", "\n", "\r", "<", ">")):
        return False
    return True


def normalize_url(value: str) -> str:
    """Lowercase scheme/host, strip surrounding whitespace."""
    value = value.strip()
    if "://" not in value:
        value = "https://" + value
    parsed = urlparse(value)
    netloc = parsed.netloc.lower()
    return parsed._replace(netloc=netloc, fragment="").geturl()


EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def is_valid_email(value: str) -> bool:
    return bool(value and EMAIL_RE.match(value.strip()) and len(value) <= 320)


def sanitize_text(value: str, max_len: int = 100_000) -> str:
    """Strip control characters from user-supplied text."""
    cleaned = "".join(ch for ch in value if ch == "\n" or ord(ch) >= 32)
    return cleaned[:max_len]
