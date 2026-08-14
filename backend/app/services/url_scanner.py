"""URL scanner: full-stack analysis of a URL or web page.

Performs transport checks (HTTPS/SSL), reputation checks (WHOIS/DNS,
typosquatting, blacklist), obfuscation checks (shorteners, punycode, entropy,
redirects) and on-page checks (forms, scripts, iframes, mixed content,
favicon similarity).

All network operations are blocking; callers should use asyncio.to_thread().
"""
from __future__ import annotations

import asyncio
import hashlib
import re
import ssl
import socket
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse

import httpx

from app.ai.html_analyzer import HTMLAnalysis
from app.ai.url_analysis import (
    PUNYCODE_RE,
    SUSPICIOUS_TLDS,
    FREE_HOSTING_HOSTS,
    contains_suspicious_keywords,
    detect_redirect_url,
    detect_typosquatting,
    entropy_of,
    extract_tld,
    hostname_only,
    is_ip_address,
    is_shortened,
    tracking_params,
)
from app.config import settings
from app.security.safe_url import UnsafeDestination, fetch_public_url, validate_public_url

BRAND_FAVICONS = {
    "paypal": "https://www.paypal.com/favicon.ico",
    "amazon": "https://www.amazon.com/favicon.ico",
    "apple": "https://www.apple.com/favicon.ico",
    "google": "https://www.google.com/favicon.ico",
    "netflix": "https://www.netflix.com/favicon.ico",
    "microsoft": "https://www.microsoft.com/favicon.ico",
    "facebook": "https://www.facebook.com/favicon.ico",
    "instagram": "https://www.instagram.com/favicon.ico",
    "twitter": "https://www.twitter.com/favicon.ico",
    "linkedin": "https://www.linkedin.com/favicon.ico",
}

SSL_TIMEOUT = 6.0


def _ssl_info(host: str, port: int = 443) -> dict:
    """Fetch and inspect the TLS certificate for a host."""
    result = {"verified": False, "expired": False, "self_signed": False,
              "mismatch": False, "issuer": None, "subject": None, "error": None,
              "expires": None, "valid_days": None, "version": None}
    ctx = ssl.create_default_context()
    try:
        with socket.create_connection((host, port), timeout=SSL_TIMEOUT) as raw:
            with ctx.wrap_socket(raw, server_hostname=host) as sock:
                cert = sock.getpeercert()
                version = sock.version()
    except ssl.SSLCertVerificationError as exc:
        result["verified"] = False
        msg = str(exc).lower()
        if "expired" in msg:
            result["expired"] = True
        if "self.signed" in msg or "self signed" in msg:
            result["self_signed"] = True
        if "doesn't match" in msg or "hostname mismatch" in msg or "ip address mismatch" in msg:
            result["mismatch"] = True
        result["error"] = str(exc)[:300]
        # try again without verification to extract dates/issuer
        return _ssl_info_unverified(host, port, result)
    except OSError as exc:
        result["error"] = str(exc)[:300]
        return result

    result["verified"] = True
    result["version"] = version
    if "notAfter" in cert:
        try:
            expires = datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z")
            expires = expires.replace(tzinfo=timezone.utc)
            result["expires"] = expires.isoformat()
            result["valid_days"] = int((expires - datetime.now(timezone.utc)).total_seconds() // 86400)
        except Exception:
            pass
    if "issuer" in cert:
        result["issuer"] = dict(x[0] for x in cert["issuer"])
    if "subject" in cert:
        result["subject"] = dict(x[0] for x in cert["subject"])
    return result


def _ssl_info_unverified(host: str, port: int, base: dict) -> dict:
    ctx = ssl._create_unverified_context()
    try:
        with socket.create_connection((host, port), timeout=SSL_TIMEOUT) as raw:
            with ctx.wrap_socket(raw, server_hostname=host) as sock:
                cert = sock.getpeercert()
    except Exception as exc:
        base["error"] = str(exc)[:300]
        return base
    if "issuer" in cert:
        base["issuer"] = dict(x[0] for x in cert["issuer"])
    if "subject" in cert:
        base["subject"] = dict(x[0] for x in cert["subject"])
    if "notAfter" in cert:
        try:
            expires = datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z")
            expires = expires.replace(tzinfo=timezone.utc)
            base["expires"] = expires.isoformat()
            base["valid_days"] = int((expires - datetime.now(timezone.utc)).total_seconds() // 86400)
            base["expired"] = expires < datetime.now(timezone.utc)
        except Exception:
            pass
    return base


def _whois_domain_age(domain: str) -> dict:
    """Domain age via python-whois (best effort)."""
    try:
        import whois
    except Exception:
        return {"available": True, "error": "python-whois not installed"}
    try:
        result = whois.whois(domain)
        creation = result.creation_date
        if isinstance(creation, list):
            creation = creation[0]
        expiration = result.expiration_date
        if isinstance(expiration, list):
            expiration = expiration[0]
        now = datetime.now(timezone.utc)
        age_days = None
        if creation:
            if creation.tzinfo is None:
                creation = creation.replace(tzinfo=timezone.utc)
            age_days = int((now - creation).total_seconds() // 86400)
        return {
            "available": result.status is None and creation is None,
            "creation_date": creation.isoformat() if creation else None,
            "expiration_date": expiration.isoformat() if expiration else None,
            "age_days": age_days,
            "registrar": str(result.registrar) if result.registrar else None,
            "org": str(result.org) if result.org else None,
            "name_servers": result.name_servers,
        }
    except Exception as exc:
        return {"available": False, "error": str(exc)[:200]}


def _dns_records(host: str) -> dict:
    try:
        import dns.resolver
    except Exception:
        return {"error": "dnspython not installed"}
    out: dict = {"a": [], "aaaa": [], "mx": [], "ns": [], "txt": []}
    for rtype, key in (("A", "a"), ("AAAA", "aaaa"), ("MX", "mx"), ("NS", "ns"), ("TXT", "txt")):
        try:
            answers = dns.resolver.resolve(host, rtype, lifetime=4)
            for rdata in answers:
                text = str(rdata)
                if rtype == "MX":
                    text = f"{rdata.preference} {rdata.exchange}"
                out[key].append(text[:255])
        except Exception:
            continue
    out["count"] = sum(len(v) for v in out.values())
    return out


def _fetch_page(url: str) -> dict:
    """Fetch a bounded public page through the SSRF-safe acquisition boundary."""
    try:
        response = fetch_public_url(url, max_bytes=settings.max_remote_response_bytes)
        headers = response["headers"]
        content_type = headers.get("content-type", "")
        encoding = "utf-8"
        if "charset=" in content_type.lower():
            encoding = content_type.lower().split("charset=", 1)[1].split(";", 1)[0].strip() or "utf-8"
        return {
            "status": response["status"],
            "final_url": response["url"],
            "headers": headers,
            "content": response["content"].decode(encoding, errors="replace"),
            "content_type": content_type,
            "server": headers.get("server"),
            "redirect_chain": response["redirect_chain"],
            "security_headers": _security_headers(headers),
            "has_cors_policy": bool(headers.get("access-control-allow-origin")),
            "resolved_addresses": response["resolved_addresses"],
        }
    except UnsafeDestination as exc:
        return {"error": str(exc)[:300], "status": 0, "content": "", "headers": {}, "redirect_chain": [], "blocked": True}
    except Exception as exc:  # pragma: no cover
        return {"error": str(exc)[:300], "status": 0, "content": "", "headers": {}, "redirect_chain": []}


def _security_headers(headers) -> dict:
    checks = {
        "Content-Security-Policy": bool(headers.get("content-security-policy")),
        "X-Frame-Options": bool(headers.get("x-frame-options")),
        "Strict-Transport-Security": bool(headers.get("strict-transport-security")),
        "X-Content-Type-Options": bool(headers.get("x-content-type-options")),
        "Referrer-Policy": bool(headers.get("referrer-policy")),
    }
    return checks


def _robots_txt(base_url: str) -> dict:
    try:
        response = fetch_public_url(urljoin(base_url, "/robots.txt"), max_bytes=100_000, max_redirects=2)
        if response["status"] == 200:
            text = response["content"].decode("utf-8", errors="replace")
            blocked = "disallow: /" in text.lower()
            return {"present": True, "blocks_all": blocked, "sample": text[:400]}
    except UnsafeDestination:
        return {"present": False, "blocked": True}
    except Exception:
        pass
    return {"present": False}


def _favicon_analysis(base_url: str, brand: str | None) -> dict:
    """Compare the site favicon against the impersonated brand's favicon."""
    if not brand:
        return {"compared": False}
    real_favicon = BRAND_FAVICONS.get(brand)
    if not real_favicon:
        return {"compared": False}
    site_hash = _fetch_favicon_hash(base_url)
    real_hash = _fetch_favicon_hash(real_favicon)
    if site_hash and real_hash:
        similarity = _hamming_similarity(site_hash, real_hash)
        return {"compared": True, "similarity": round(similarity, 3), "site_hash": site_hash}
    return {"compared": False}


def _fetch_favicon_hash(url: str) -> str | None:
    try:
        target = urljoin(url, "/favicon.ico") if not url.startswith("http") else url
        response = fetch_public_url(target, accept="image/*,*/*;q=0.8", max_bytes=512_000, max_redirects=2)
        if response["status"] != 200:
            return None
        content = response["content"]
        try:
            from PIL import Image
            from io import BytesIO

            image = Image.open(BytesIO(content)).convert("L").resize((16, 16))
            pixels = list(image.getdata())
            avg = sum(pixels) / len(pixels)
            bits = "".join("1" if p >= avg else "0" for p in pixels)
            return bits
        except Exception:
            return hashlib.sha256(content).hexdigest()[:32]
    except Exception:
        return None


def _hamming_similarity(a: str, b: str) -> float:
    if len(a) != len(b):
        return 0.0
    matches = sum(1 for x, y in zip(a, b) if x == y)
    return matches / len(a)


def _safe_domain_list(host: str) -> list[str]:
    parts = host.split(".")
    out = []
    for i in range(len(parts) - 1, 0, -1):
        out.append(".".join(parts[i - 1:]))
    return out


async def scan_url(url: str, known_threats: list[str] | None = None) -> dict:
    """Async entry point; runs the blocking analysis in a worker thread."""
    known_threats = known_threats or []
    return await asyncio.to_thread(_scan_url_sync, url, known_threats)


def _scan_url_sync(url: str, known_threats: list[str] | None = None) -> dict:
    known_threats = known_threats or []
    findings: list[dict] = []
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    scheme = parsed.scheme.lower()
    final_url = url

    def add(code, category, title, description, severity, evidence=None, confidence=0.8, extra=None):
        findings.append({
            "code": code, "category": category, "title": title,
            "description": description, "severity": severity, "evidence": evidence,
            "confidence": confidence, "extra": extra or {},
        })

    # Validate the initial destination before any transport, DNS, or content
    # request. Lexical analysis on private targets is not useful enough to
    # justify turning AEGIS into a private-network probe.
    try:
        initial_destination = validate_public_url(url)
    except UnsafeDestination as exc:
        add("unsafe_destination", "security", "Unsafe destination blocked",
            "AEGIS refused to fetch a private, reserved, malformed, or non-web destination.",
            "critical", str(exc), 0.99, {"source": "safe_fetch", "network_fetch": "blocked"})
        return {
            "findings": findings,
            "meta": {
                "url": url, "host": host, "final_url": url, "status_code": 0,
                "network_fetch": "blocked", "block_reason": str(exc)[:300],
                "redirect_chain": [],
            },
        }

    # ---- 1. Transport -----------------------------------------------------
    if scheme == "https":
        add("https_secure", "transport", "HTTPS enabled",
            "The site is served over an encrypted HTTPS connection.", "safe")
    else:
        add("http_insecure", "transport", "Insecure HTTP",
            "The site is served over plain HTTP without encryption.", "high")

    ssl_info = {}
    try:
        ssl_info = _ssl_info(host)
    except Exception:
        pass
    if ssl_info:
        if ssl_info.get("verified"):
            add("ssl_cert_valid", "transport", "Valid SSL certificate",
                "The SSL certificate is valid and trusted.", "safe", confidence=0.9)
        else:
            if ssl_info.get("expired"):
                add("ssl_cert_expired", "transport", "Expired SSL certificate",
                    "The SSL certificate has expired.", "medium", ssl_info.get("error"), 0.9)
            if ssl_info.get("self_signed"):
                add("ssl_self_signed", "transport", "Self-signed certificate",
                    "The certificate is self-signed, unusual for legitimate services.",
                    "medium", ssl_info.get("error"), 0.8)
            if ssl_info.get("mismatch"):
                add("ssl_cert_mismatch", "transport", "Certificate hostname mismatch",
                    "The certificate does not match the domain.", "high", ssl_info.get("error"), 0.9)
            if not (ssl_info.get("expired") or ssl_info.get("self_signed") or ssl_info.get("mismatch")):
                add("ssl_cert_untrusted", "transport", "Untrusted certificate",
                    "The certificate is not trusted by the system CA store.",
                    "high", ssl_info.get("error"), 0.8)

    # ---- 2. Address form ---------------------------------------------------
    if is_ip_address(host):
        add("ip_address_url", "obfuscation", "IP address instead of domain",
            "The link points directly to an IP address.", "high", host, 0.95)
    if PUNYCODE_RE.search(host):
        add("punycode", "impersonation", "Punycode / homograph attack",
            "The domain uses non-ASCII characters that can imitate latin letters.",
            "high", host, 0.9)
    if "@" in url:
        add("url_entropy_high", "obfuscation", "Suspicious '@' in URL",
            "The address embeds an @ symbol to hide the true host.", "high", url[:120], 0.8)
    if parsed.port:
        add("url_entropy_high", "obfuscation", "Non-standard port",
            "The URL uses a non-standard port.", "medium", str(parsed.port), 0.6)

    short, short_host = is_shortened(url)
    if short:
        # Check if this is a legitimate domain using a shortener for tracking
        # Major brands sometimes use shorteners for legitimate tracking
        major_brands = ("microsoft", "google", "amazon", "apple", "netflix", "facebook", "twitter", "linkedin")
        is_major_brand = any(b in host for b in major_brands)
        if not is_major_brand:
            add("shortened_url", "obfuscation", "Shortened link",
                "The link is a URL shortener hiding the destination.", "low", short_host, 0.9)

    open_redir, target = detect_redirect_url(url)
    if open_redir:
        add("open_redirect", "obfuscation", "Open redirect",
            "The link carries a redirect parameter to another site.", "medium", target, 0.9)

    tld = extract_tld(host)
    if tld in SUSPICIOUS_TLDS:
        add("suspicious_tld", "reputation", "Suspicious top-level domain",
            f"'{tld}' is a TLD frequently abused by scammers.", "medium", tld, 0.85)

    if any(h in host for h in FREE_HOSTING_HOSTS):
        add("free_hosting", "reputation", "Free hosting domain",
            "The site runs on a free-hosting platform commonly abused by scammers.",
            "medium", host, 0.7)

    # ---- 3. Brand / typosquatting -----------------------------------------
    brand, similarity = detect_typosquatting(host)
    # Only flag if similarity is high and it's not a legitimate domain
    if brand and similarity >= 0.78:
        # Check if this is actually the real domain for this brand
        is_legitimate = (
            host == brand or 
            host == f"www.{brand}" or 
            host == f"{brand}.com" or 
            host == f"www.{brand}.com" or
            host.endswith(f".{brand}.com")
        )
        if not is_legitimate:
            add("typosquatting", "impersonation", "Typosquatting",
                f"This domain looks like it is imitating '{brand}'.",
                "critical", host, 0.95, {"brand": brand, "similarity": similarity})

    # exact brand match
    known_brand = None
    for candidate in ("paypal", "amazon", "apple", "google", "netflix",
                      "microsoft", "facebook", "instagram", "twitter", "linkedin"):
        if host == f"{candidate}.com" or host.endswith(f".{candidate}.com"):
            known_brand = candidate
            break
    if known_brand and scheme == "https":
        add("brand_confirmed", "reputation", "Legitimate domain match",
            f"The domain exactly matches the legitimate brand '{known_brand}'.",
            "safe", host, 0.95)

    # ---- 4. Entropy / keywords / tracking ----------------------------------
    ent = entropy_of(host + parsed.path)
    if ent > 4.2:
        add("url_entropy_high", "obfuscation", "High URL entropy",
            "The address contains many random-looking characters.",
            "low", f"entropy={ent:.2f}", 0.6)

    suspicious_kw = contains_suspicious_keywords(url)
    if suspicious_kw:
        add("suspicious_keywords_url", "obfuscation", "Suspicious keywords in URL",
            "The address contains words commonly found in phishing links.",
            "high", ", ".join(suspicious_kw[:6]), 0.8)

    trackers = tracking_params(parsed)
    if trackers:
        add("tracking_params", "obfuscation", "Tracking parameters present",
            "The link contains tracking parameters.", "info", ", ".join(trackers[:5]), 0.9)

    # ---- 5. Known threat / reputation --------------------------------------
    host_chain = _safe_domain_list(host)
    matched_threat = None
    for t in known_threats:
        tl = t.lower()
        if tl in host_chain or host in tl or tl == host:
            matched_threat = t
            break
    if matched_threat:
        add("known_threat", "reputation", "Known threat match",
            "This address is already known to be malicious and has been blocked.",
            "critical", matched_threat, 0.99)

    # ---- 6. WHOIS / DNS -----------------------------------------------------
    whois_info = {}
    try:
        whois_info = _whois_domain_age(host)
    except Exception:
        pass
    age_days = whois_info.get("age_days")
    if age_days is not None:
        if age_days > 365 * 5:
            add("domain_very_old", "reputation", "Long-established domain",
                "The domain has existed for more than five years.", "safe",
                f"{age_days} days old", 0.8)
        elif age_days > 365:
            add("domain_old", "reputation", "Established domain",
                "The domain has existed for more than a year.", "safe",
                f"{age_days} days old", 0.7)
        elif age_days > 30:
            add("domain_young", "reputation", "Recently registered domain",
                "The domain was registered recently (less than a year old).",
                "info", f"{age_days} days old", 0.3)
        else:
            # Domain younger than 7 days - more concerning
            if age_days < 7:
                severity = "high"
                confidence = 0.8
                description = "The domain was registered in the last 7 days - extremely new, often used for scam sites."
            elif age_days < 14:
                severity = "medium"
                confidence = 0.7
                description = "The domain was registered within the last 14 days."
            else:
                severity = "low"
                confidence = 0.6
                description = "The domain was registered within the last 30 days."
            add("domain_fresh", "reputation", "Very new domain",
                description,
                severity, f"{age_days} days old", confidence)

    dns = {}
    try:
        dns = _dns_records(host)
    except Exception:
        pass
    dns_count = dns.get("count", 0)
    if not ssl_info.get("verified") and dns_count == 0 and not whois_info.get("error"):
        add("no_content", "code", "Domain appears unregistered",
            "No DNS records were found for this domain.", "high", host, 0.6)

    # ---- 7. Page fetch & content analysis -----------------------------------
    page = _fetch_page(url)
    page_url = url
    if page.get("blocked"):
        add("unsafe_destination", "security", "Unsafe redirect blocked",
            "A redirect or linked fetch target was blocked by AEGIS network safety policy.",
            "high", page.get("error"), 0.99,
            {"source": "safe_fetch", "network_fetch": "blocked"})
    if page.get("final_url") and page["final_url"] != url:
        page_url = page["final_url"]
        final_parsed = urlparse(page_url)
        final_host = (final_parsed.hostname or "").lower()
        if final_host != host:
            add("hidden_redirect", "obfuscation", "Hidden redirect",
                "The page redirects to a different domain.",
                "high", f"{url} -> {page_url}", 0.9)
            brand2, _ = detect_typosquatting(final_host)
            if brand2:
                add("typosquatting", "impersonation", "Typosquatting (redirect target)",
                    f"The redirect target looks like it is imitating '{brand2}'.",
                    "critical", final_host, 0.9)

    chain = page.get("redirect_chain") or []
    if len(chain) >= 3:
        add("hidden_redirect", "obfuscation", "Long redirect chain",
            "The URL passes through multiple redirects before reaching its target.",
            "medium", " -> ".join(chain[:5]), 0.7)

    robots = _robots_txt(url)
    # Only flag if robots.txt explicitly blocks all crawlers AND it's not a major brand
    if robots.get("present") and robots.get("blocks_all"):
        # Major brands often have legitimate reasons to block certain paths
        major_brands = ("google", "facebook", "amazon", "microsoft", "apple", "netflix", "twitter", "instagram")
        is_major_brand = any(b in host for b in major_brands)
        if not is_major_brand:
            add("robots_blocked", "code", "Search engines blocked",
                "The site asks search engines not to index it.", "low", None, 0.6)

    content = page.get("content") or ""
    if content:
        analysis = HTMLAnalysis(content, base_url=page_url)
        # Only flag login forms on non-brand domains or if the domain doesn't match the brand
        if analysis.has_login_form:
            # Check if this is a legitimate login page for a major brand
            major_brands = ("google", "facebook", "amazon", "microsoft", "apple", "netflix", "twitter", "instagram", "linkedin")
            is_legitimate_login = any(b in host for b in major_brands)
            if not is_legitimate_login:
                add("login_form", "credential", "Login form present",
                    "The page contains a login form that could capture credentials.",
                    "info", None, 0.7)
        if analysis.payment_request:
            # Check if this is a legitimate e-commerce or brand page
            major_brands = ("microsoft", "amazon", "apple", "netflix", "adobe", "spotify", "paypal")
            is_legitimate_payment = any(b in host for b in major_brands) or "shop" in host or "store" in host
            if not is_legitimate_payment:
                add("payment_request", "credential", "Payment request on page",
                    "The page asks for payment or card details.",
                    "high", None, 0.8)
            else:
                # Still add as info-level for legitimate sites
                add("payment_request", "credential", "Payment options available",
                    "The page offers payment/purchase options, which is normal for commercial sites.",
                    "info", None, 0.5)
        external = analysis.external_scripts
        if external:
            # Legitimate CDNs and analytics domains
            legit_external = (
                "cdnjs.cloudflare.com", "cdn.jsdelivr.net", "unpkg.com", "fonts.googleapis.com", 
                "kit.fontawesome.com", "code.jquery.com", "cdn.tailwindcss.com", "giscus.app",
                "microsoft.com", "adobe.com", "google.com", "googleapis.com", "gstatic.com",
                "cloudflare.com", "amazonaws.com", "cloudfront.net", "akamai.net", "fastly.net",
                "rum.hlx.page", "uhf.microsoft.com", "wcpstatic.microsoft.com"
            )
            suspicious_external = [e for e in external if not any(cdn in e.lower() for cdn in legit_external)]
            if suspicious_external:
                add("external_scripts", "code", "External scripts loaded",
                    "The page loads scripts from external domains.",
                    "info", ", ".join(suspicious_external[:4]), 0.4)
        obfuscated = analysis.obfuscated_js
        if obfuscated:
            # Major brands use minified JS for performance - this is normal
            major_brands = ("google", "facebook", "amazon", "microsoft", "apple", "netflix", "twitter", "instagram", "linkedin")
            is_major_brand = any(b in host for b in major_brands)
            # Only flag if it's not a major brand OR if the obfuscation is extreme (contains eval/atob)
            extreme_obfuscation = any("eval()" in o or "atob()" in o for o in obfuscated)
            if not is_major_brand or extreme_obfuscation:
                add("js_obfuscated", "code", "Obfuscated JavaScript",
                    "The page contains heavily obfuscated JavaScript.",
                    "high" if extreme_obfuscation else "medium", ", ".join(obfuscated[:4]), 0.8)
        hidden_iframes = analysis.hidden_iframes
        if hidden_iframes:
            add("hidden_iframe", "code", "Hidden iframe",
                "The page embeds invisible iframes, a classic phishing technique.",
                "high", str(hidden_iframes[:2]), 0.85)
        mixed = analysis.mixed_content
        if mixed:
            add("mixed_content", "code", "Mixed content",
                "The secure page loads insecure HTTP resources.",
                "medium", ", ".join(mixed[:4]), 0.7)
        if analysis.collector.meta_refresh:
            add("meta_refresh", "obfuscation", "Meta refresh redirect",
                "The page auto-redirects after a few seconds.",
                "medium", analysis.collector.meta_refresh_url or None, 0.7)
        hidden_forms = analysis.hidden_forms
        if hidden_forms:
            add("hidden_form", "code", "Hidden form",
                "The page contains forms hidden from view.",
                "medium", str(hidden_forms[:2]), 0.75)
        if analysis.is_empty:
            add("no_content", "code", "Empty or minimal content",
                "The page has almost no content, common for quickly-created scam pages.",
                "low", None, 0.6)

        # Brand impersonation: page mentions brands but is NOT the brand domain
        page_brands = analysis.brand_terms
        for pb in page_brands:
            is_real = host == f"{pb.replace(' ', '')}.com" or f".{pb.replace(' ', '')}.com" in host
            if not is_real:
                add("brand_impersonation", "impersonation", "Brand impersonation",
                    f"The page claims to be from '{pb}' but is not hosted by them.",
                    "critical", f"'{pb}' mentioned on non-brand domain", 0.8, {"brand": pb})
                break

        # Favicon comparison against impersonated brand
        favicon_brand = None
        for fbrand in ("paypal", "amazon", "apple", "google", "netflix",
                       "microsoft", "facebook", "instagram", "twitter", "linkedin"):
            if fbrand in host:
                favicon_brand = fbrand
                break
        if favicon_brand:
            favicon = _favicon_analysis(page_url, favicon_brand)
            if favicon.get("compared") and favicon["similarity"] >= 0.75:
                add("favicon_mismatch", "impersonation", "Favicon impersonation",
                    "The site imitates the favicon of a well-known brand.",
                    "medium", f"similarity={favicon['similarity']:.0%}", 0.7)

        if not page.get("status"):
            add("no_content", "code", "Page unreachable",
                "The page could not be fetched for content analysis.",
                "medium", page.get("error"), 0.6)

    return {
        "findings": findings,
        "meta": {
            "url": url,
            "host": host,
            "final_url": page_url,
            "status_code": page.get("status"),
            "ssl": ssl_info,
            "whois": {k: v for k, v in whois_info.items() if k != "name_servers"},
            "dns": dns,
            "security_headers": page.get("security_headers", {}),
            "server": page.get("server"),
            "content_type": page.get("content_type"),
            "redirect_chain": chain,
            "network_fetch": "blocked" if page.get("blocked") else "completed",
            "resolved_addresses": page.get("resolved_addresses", list(initial_destination.addresses)),
        },
    }
