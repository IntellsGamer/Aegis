"""Lightweight HTML analysis using only the standard library.

Detects: forms, hidden forms/iframes, external scripts, inline scripts,
meta refresh, mixed content, login/payment keywords and JS obfuscation.
"""
from __future__ import annotations

import re
from html.parser import HTMLParser
from urllib.parse import urlparse

ATTR_MAPPING = {"class": "class_", "for": "for_"}

LOGIN_KEYWORDS = [
    "username", "userid", "email", "password", "passwd", "login", "signin",
    "sign in", "log in", "otp", "one-time", "verification code",
]

PAYMENT_KEYWORDS = [
    "card number", "credit card", "debit card", "cvv", "expiry", "expiration",
    "cardholder", "billing address", "payment", "pay now", "card details",
    "visa", "mastercard", "iban", "swift",
]

BRAND_LOOKALIKE_TERMS = [
    "paypal", "amazon", "apple", "netflix", "microsoft", "google", "facebook",
    "bank", "visa", "mastercard", "chase", "wells fargo", "bank of america",
]


class _Collector(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.forms: list[dict] = []
        self.iframes: list[dict] = []
        self.scripts_src: list[str] = []
        self.inline_scripts: list[str] = []
        self.meta_refresh: bool = False
        self.meta_refresh_url: str | None = None
        self.links: list[dict] = []
        self.style_tags: int = 0
        self.base_href: str | None = None
        self._current_script: list[str] = []
        self._in_script = False

    def _attrs(self, attrs: list[tuple[str, str | None]]) -> dict:
        out: dict = {}
        for key, value in attrs:
            if value is None:
                continue
            out[key.lower()] = value
        return out

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = self._attrs(attrs)
        if tag == "form":
            self.forms.append(
                {"action": a.get("action"), "method": a.get("method", "get"), "attrs": a}
            )
        elif tag == "iframe":
            self.iframes.append(
                {
                    "src": a.get("src"),
                    "width": a.get("width"),
                    "height": a.get("height"),
                    "hidden": a.get("hidden") is not None
                    or (a.get("style") and "display:none" in (a.get("style") or "").replace(" ", ""))
                    or (a.get("width") in ("0", "1px") and a.get("height") in ("0", "1px")),
                }
            )
        elif tag == "script":
            if a.get("src"):
                self.scripts_src.append(a["src"])
            self._current_script = []
            self._in_script = True
        elif tag == "meta":
            if a.get("http-equiv", "").lower() == "refresh":
                self.meta_refresh = True
                content = a.get("content", "")
                m = re.search(r"url\s*=\s*(.+)", content, re.IGNORECASE)
                self.meta_refresh_url = m.group(1).strip().strip("'\"") if m else None
        elif tag == "link":
            self.links.append({"href": a.get("href"), "rel": a.get("rel")})
        elif tag == "style":
            self.style_tags += 1
        elif tag == "base":
            self.base_href = a.get("href")

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self._in_script:
            self.inline_scripts.append("".join(self._current_script))
            self._in_script = False

    def handle_data(self, data: str) -> None:
        if self._in_script:
            self._current_script.append(data)


class HTMLAnalysis:
    def __init__(self, html: str, base_url: str | None = None) -> None:
        self.html = html
        self.base_url = base_url
        self.collector = _Collector()
        try:
            self.collector.feed(html)
        except Exception:
            pass
        self.text = _strip_tags(html)
        self.lower_text = self.text.lower()

    # --- presence checks --------------------------------------------------
    @property
    def has_login_form(self) -> bool:
        if any(any(k in str(f.get("action", "")).lower() for k in LOGIN_KEYWORDS) for f in self.collector.forms):
            return True
        return any(k in self.lower_text for k in ("password", "log in", "sign in"))

    @property
    def payment_request(self) -> bool:
        return any(k in self.lower_text for k in PAYMENT_KEYWORDS)

    @property
    def hidden_iframes(self) -> list[dict]:
        return [i for i in self.collector.iframes if i["hidden"]]

    @property
    def external_scripts(self) -> list[str]:
        return [s for s in self.collector.scripts_src if s and _is_external(s, self.base_url)]

    @property
    def hidden_forms(self) -> list[dict]:
        return [f for f in self.collector.forms if _form_hidden(f)]

    @property
    def obfuscated_js(self) -> list[str]:
        out: list[str] = []
        code = "\n".join(self.collector.inline_scripts)
        patterns = [
            (r"\beval\s*\(", "eval() usage"),
            (r"\batob\s*\(", "atob() base64 decoding"),
            (r"fromCharCode", "char-code obfuscation"),
            (r"\\x[0-9a-fA-F]{2,}", "hex-escaped strings"),
            (r"document\.write\s*\(", "dynamic document.write"),
            (r"[a-zA-Z_$][\w$]{20,}\s*=\s*[a-zA-Z_$][\w$]{20,}", "long variable chains"),
            (r"unescape\s*\(", "unescape() usage"),
        ]
        for pattern, label in patterns:
            if re.search(pattern, code):
                out.append(label)
        return out

    @property
    def mixed_content(self) -> list[str]:
        if not self.base_url or not self.base_url.lower().startswith("https"):
            return []
        return [
            ref for ref in (self.collector.scripts_src + [l["href"] for l in self.collector.links])
            if ref and ref.startswith("http://")
        ]

    @property
    def brand_terms(self) -> list[str]:
        return [b for b in BRAND_LOOKALIKE_TERMS if b in self.lower_text]

    @property
    def is_empty(self) -> bool:
        return len(self.text.strip()) < 40

    def count(self, item: str) -> int:
        return self.lower_text.count(item)


def _strip_tags(html: str) -> str:
    html = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.IGNORECASE | re.DOTALL)
    html = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", html)


def _is_external(url: str, base_url: str | None) -> bool:
    parsed = urlparse(url)
    if parsed.scheme or parsed.netloc:
        if not base_url:
            return True
        base = urlparse(base_url)
        return (parsed.hostname or "").lower() != (base.hostname or "").lower()
    return False


def _form_hidden(form: dict) -> bool:
    attrs = form.get("attrs", {})
    style = attrs.get("style", "")
    return (
        "display:none" in style.replace(" ", "")
        or "visibility:hidden" in style
        or "hidden" in attrs
        or attrs.get("width") in ("0", "1")
    )
