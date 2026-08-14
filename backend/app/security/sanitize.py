"""Input sanitization helpers (XSS / injection defense-in-depth)."""
from __future__ import annotations

import html
import re
from urllib.parse import quote

_SCRIPT_TAG_RE = re.compile(
    r"<\s*(script|iframe|object|embed|applet|meta|link|style|form)[^>]*>.*?"
    r"<\s*/\s*\1\s*>",
    re.IGNORECASE | re.DOTALL,
)
_EVENT_RE = re.compile(
    r"""\son\w+\s*=|javascript\s*:|vbscript\s*:|data\s*:\s*text/html""",
    re.IGNORECASE,
)


def sanitize_html(value: str) -> str:
    """Escape a string intended for HTML insertion (always prefer text())."""
    return html.escape(value, quote=True)


def strip_dangerous_tags(value: str) -> str:
    """Best-effort removal of executable markup; main defense is templating."""
    value = _SCRIPT_TAG_RE.sub("", value)
    value = _EVENT_RE.sub("", value)
    return value


def urlencode_path(value: str) -> str:
    return quote(value, safe="/")


def sanitize_filename(value: str, default: str = "file") -> str:
    """Strip path separators and control characters from a filename."""
    value = value.replace("\\", "/").split("/")[-1]
    value = re.sub(r"[\x00-\x1f\x7f]", "", value).strip()
    if not value or value in (".", ".."):
        return default
    return value[:200]
