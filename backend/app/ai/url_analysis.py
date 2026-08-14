"""Pure URL analysis helpers (no network I/O). Used by the URL scanner and
the ML URL feature extractor."""
from __future__ import annotations

import difflib
import math
import re
import socket
from urllib.parse import parse_qs, unquote, urlparse

BRANDS: list[str] = [
    "paypal", "amazon", "apple", "icloud", "netflix", "microsoft", "office",
    "google", "gmail", "facebook", "instagram", "whatsapp", "twitter", "x",
    "linkedin", "tiktok", "youtube", "facebook", "ebay", "visa", "mastercard",
    "americanexpress", "amex", "chase", "wellsfargo", "bankofamerica", "citi",
    "hsbc", "barclays", "revolut", "wise", "stripe", "payoneer", "skrill",
    "steam", "epicgames", "discord", "telegram", "binance", "coinbase",
    "cryptocom", "robinhood", "dell", "hp", "lenovo", "samsung", "nokia",
    "spotify", "adobe", "dropbox", "bitcoin", "ethereum", "dhl", "fedex",
    "ups", "usps", "royalmail", "irs", "gov", "ssa", "socialsecurity",
    "alibaba", "aliexpress", "shein", "zalando", "indeed", "airbnb", "uber",
]

# TLDs heavily abused by phishing/scam campaigns.
SUSPICIOUS_TLDS: set[str] = {
    ".tk", ".ml", ".ga", ".cf", ".gq", ".xyz", ".top", ".club", ".work",
    ".online", ".site", ".icu", ".pw", ".info", ".buzz", ".click", ".link",
    ".live", ".loan", ".accountant", ".download", ".racing", ".stream",
    ".review", ".win", ".party", ".date", ".science", ".cam", ".vip",
}

FREE_HOSTING_HOSTS: set[str] = {
    "wordpress.com", "blogspot.com", "wixsite.com", "weebly.com", "webs.com",
    "squarespace.com", "github.io", "gitlab.io", "netlify.app", "vercel.app",
    "pages.dev", "webflow.io", "strikingly.com", "carrd.co", "godaddysites.com",
    "blogger.com", "tumblr.com", "000webhostapp.com", "infinityfree.net",
    "weebly.com",
}

SHORTENER_HOSTS: set[str] = {
    "bit.ly", "t.co", "tinyurl.com", "goo.gl", "is.gd", "buff.ly", "ow.ly",
    "shorturl.at", "rb.gy", "cutt.ly", "rebrand.ly", "t.ly", "s.id", "zurl.co",
    "tiny.cc", "shorte.st", "tinyurl.co.uk", "qrco.de", "taplink.cc", "lnkd.in",
}

# Keywords strongly associated with phishing pages.
SUSPICIOUS_KEYWORDS: list[str] = [
    "login", "signin", "sign-in", "verify", "verification", "secure", "security",
    "account", "confirm", "update", "unlock", "wallet", "password", "credential",
    "banking", "suspend", "blocked", "disabled", "alert", "invoice", "refund",
    "reward", "bonus", "prize", "free", "win", "claim", "track", "unusual",
    "authenticate", "required", "billing", "renew", "gift", "bonus", "crypto",
]

SUSPICIOUS_PATH_KEYWORDS: list[str] = [
    "login", "verify", "signin", "secure", "confirm", "update", "auth",
    "unlock", "wallet", "password", "suspend", "blocked", "refund", "invoice",
    "activate", "validate", "renew", "checkout",
]

IPV4_RE = re.compile(r"^\d{1,3}(\.\d{1,3}){3}$")
HEX_IP_RE = re.compile(r"^0x[0-9a-f]+$", re.IGNORECASE)
PUNYCODE_RE = re.compile(r"^xn--", re.IGNORECASE)


def extract_url_features(url: str) -> dict:
    """Lightweight synchronous feature vector used by the ML URL model."""
    parsed = urlparse(url if "://" in url else "https://" + url)
    host = parsed.hostname or ""
    host_lower = host.lower()
    path = parsed.path
    num_dots = host.count(".")
    num_digits = sum(c.isdigit() for c in host)
    num_dashes = host.count("-")
    num_subdomains = max(len(host.split(".")) - 2, 0)
    entropy = round(entropy_of(host + path), 3)
    has_ip = is_ip_address(host)
    has_port = parsed.port is not None
    https = parsed.scheme.lower() == "https"
    punycode = bool(PUNYCODE_RE.search(host_lower))
    tld = extract_tld(host_lower)
    suspicious_tld = tld in SUSPICIOUS_TLDS if tld else False
    shortener = host_lower in SHORTENER_HOSTS or any(h in host_lower for h in SHORTENER_HOSTS)
    typosquat, _ = detect_typosquatting(host_lower)
    lower_url = url.lower()
    return {
        "url_len": float(len(url)),
        "host_len": float(len(host)),
        "path_len": float(len(path)),
        "num_dots": float(num_dots),
        "num_digits": float(num_digits),
        "num_dashes": float(num_dashes),
        "num_subdomains": float(num_subdomains),
        "entropy": float(entropy),
        "has_ip": float(has_ip),
        "has_port": float(has_port),
        "https": float(https),
        "punycode": float(punycode),
        "suspicious_tld": float(suspicious_tld),
        "shortener": float(shortener),
        "typosquat": float(bool(typosquat)),
        "brand_word": float(any(b in lower_url for b in BRANDS)),
        "login_word": float(any(k in lower_url for k in ("login", "signin", "sign-in"))),
        "pay_word": float(any(k in lower_url for k in ("pay", "payment", "invoice", "refund"))),
        "verify_word": float(any(k in lower_url for k in ("verify", "verification", "confirm", "secure"))),
        "free_word": float(any(k in lower_url for k in ("free", "win", "prize", "reward", "claim"))),
        "double_slash": float("//" in path or "//" in (parsed.netloc or "")),
        "at_sign": float("@" in url),
        "random_path": float(len(path) > 0 and re.search(r"[0-9]{6,}", path) is not None),
    }


def entropy_of(text: str) -> float:
    if not text:
        return 0.0
    counts: dict[str, int] = {}
    for ch in text:
        counts[ch] = counts.get(ch, 0) + 1
    total = len(text)
    ent = 0.0
    for count in counts.values():
        p = count / total
        ent -= p * math.log2(p)
    return ent


def is_ip_address(host: str) -> bool:
    host = host.strip("[]")
    if IPV4_RE.match(host):
        parts = [int(p) for p in host.split(".")]
        if all(0 <= p <= 255 for p in parts):
            return True
    if HEX_IP_RE.match(host):
        return True
    return False


def extract_tld(host: str) -> str:
    parts = host.split(".")
    if len(parts) >= 2:
        return "." + parts[-1].lower()
    return ""


def detect_typosquatting(host: str) -> tuple[str | None, float]:
    """Return a likely impersonated brand from the registrable hostname label.

    A comparison across the whole hostname is deceptively unsafe: it turns a
    short brand token such as ``x`` into a match for ordinary domains including
    ``example.com``.  Only the effective domain label and its dash/underscore
    tokens are relevant to this lexical signal.  Remote reputation and page
    evidence remain separate signals in the fusion engine.
    """
    host = host.lower().strip(".")
    labels = [label for label in host.split(".") if label]
    if len(labels) < 2:
        return None, 0.0

    # This intentionally conservative extraction handles ordinary TLDs. It is
    # a lexical heuristic, not an assertion about PSL ownership.
    domain_label = labels[-2]
    tokens = [token for token in re.split(r"[-_]", domain_label) if token]

    for brand in BRANDS:
        # Very short names are too collision-prone for generic substring or
        # edit-distance checks. They can still be assessed by other evidence.
        if len(brand) < 4:
            continue
        if host == f"{brand}.com" or host == f"www.{brand}.com" or host.endswith(f".{brand}.com"):
            continue

        # A full brand token or compound root label is a strong lexical cue.
        if brand in domain_label:
            return brand, 0.95

        # Check keyboard-style mutations on individual domain tokens rather
        # than the entire hostname, e.g. paypa1-login.example -> paypal.
        for token in tokens:
            if len(token) < 4 or abs(len(token) - len(brand)) > 2:
                continue
            ratio = difflib.SequenceMatcher(None, token, brand).ratio()
            if ratio >= 0.82:
                return brand, ratio

    return None, 0.0


def is_shortened(url: str) -> tuple[bool, str | None]:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if host in SHORTENER_HOSTS or any(h in host for h in SHORTENER_HOSTS):
        return True, host
    return False, None


def contains_suspicious_keywords(url: str) -> list[str]:
    lower = url.lower()
    return [k for k in SUSPICIOUS_KEYWORDS if re.search(rf"\b{re.escape(k)}\b", lower)]


def tracking_params(parsed) -> list[str]:
    params = parse_qs(parsed.query)
    trackers = [
        "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
        "ref", "referrer", "source", "affiliate", "clickid", "gclid", "fbclid",
    ]
    return [p for p in trackers if p in params]


def looks_like_brand_page(html_text: str, brand: str | None) -> bool:
    if not brand:
        return False
    return brand.lower() in html_text.lower()


def detect_redirect_url(url: str) -> tuple[bool, str | None]:
    """Detect obvious redirect-payload URLs like /r?url=https://evil."""
    parsed = urlparse(url)
    for key in ("url", "redirect", "next", "return", "dest", "continue", "u", "link", "target"):
        value = parse_qs(parsed.query).get(key)
        if value:
            candidate = unquote(value[0])
            if candidate.startswith(("http://", "https://", "//")):
                return True, candidate
    return False, None


def hostname_only(url: str) -> str:
    return (urlparse(url).hostname or "").lower()


def root_domain(host: str) -> str:
    parts = host.split(".")
    if len(parts) <= 2:
        return host
    # crude: drop leading subdomain labels (handles co.uk poorly, acceptable)
    return ".".join(parts[-2:])


def randomize_ip(host: str) -> str:
    """Best-effort resolve for tests/local; production uses real DNS."""
    try:
        return socket.gethostbyname(host)
    except Exception:
        return ""
