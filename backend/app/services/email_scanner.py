"""Email scanner: header/authentication analysis + body scanning.

Uses only the standard library email module so raw .eml files and pasted
headers are handled without external services.
"""
from __future__ import annotations

import asyncio
import email
import email.policy
import re
from email.header import decode_header
from email.utils import parseaddr

from app.ai.text_patterns import URL_RE
from app.ai.url_analysis import detect_typosquatting, is_shortened


async def scan_email(raw: str) -> dict:
    return await asyncio.to_thread(_scan_email_sync, raw)


def _decode(value: str) -> str:
    if not value:
        return ""
    parts = decode_header(value)
    out = []
    for text, charset in parts:
        if isinstance(text, bytes):
            try:
                out.append(text.decode(charset or "utf-8", errors="replace"))
            except Exception:
                out.append(text.decode("utf-8", errors="replace"))
        else:
            out.append(text)
    return "".join(out)


def _header(msg, name: str, default: str = "") -> str:
    try:
        return str(msg.get(name, default) or default)
    except Exception:
        return default


def _auth_result(msg) -> tuple[bool, bool, bool]:
    """Best-effort SPF/DKIM/DMARC extraction from Authentication-Results."""
    raw = _header(msg, "Authentication-Results", "")
    spf = re.search(r"spf=(\w+)", raw, re.IGNORECASE)
    dkim = re.search(r"dkim=(\w+)", raw, re.IGNORECASE)
    dmarc = re.search(r"dmarc=(\w+)", raw, re.IGNORECASE)
    ok = ("pass", "none", "neutral")
    return (
        not spf or spf.group(1).lower() in ok,
        not dkim or dkim.group(1).lower() in ok,
        not dmarc or dmarc.group(1).lower() in ok,
    )


def _extract_links(body: str) -> list[str]:
    return URL_RE.findall(body)


def _extract_attachments(msg) -> list[dict]:
    attachments = []
    for part in msg.walk():
        content_disposition = str(part.get("Content-Disposition", ""))
        if "attachment" in content_disposition.lower() or part.get_filename():
            filename = _decode(part.get_filename() or "unnamed")
            ctype = part.get_content_type()
            size = len(part.get_payload(decode=True) or b"")
            attachments.append({"filename": filename, "content_type": ctype, "size": size})
    return attachments


def _sender_spoofed(display: str, real_from: str, reply_to: str) -> bool:
    """Display-name spoofing: e.g. 'PayPal Security' <random@mail.ru>."""
    name = display or ""
    brand_hint = re.search(
        r"(paypal|amazon|apple|netflix|microsoft|visa|mastercard|bank of|wells fargo|irs|gov)",
        name,
        re.IGNORECASE,
    )
    if not brand_hint:
        return False
    real_addr = parseaddr(real_from)[1]
    domain = real_addr.split("@")[-1] if "@" in real_addr else ""
    return brand_hint.group(1).lower().replace(" ", "") not in domain


def _scan_email_sync(raw: str) -> dict:
    findings: list[dict] = []

    def add(code, category, title, description, severity, evidence=None, confidence=0.8):
        findings.append({
            "code": code, "category": category, "title": title,
            "description": description, "severity": severity,
            "evidence": evidence, "impact": 0.0, "confidence": confidence,
        })

    try:
        msg = email.message_from_string(raw, policy=email.policy.default)
    except Exception:
        msg = None

    if msg is None:
        add("unknown_sender", "email_auth", "Unparsable email",
            "The email could not be parsed.", "medium")
        return {"findings": findings, "meta": {"parsed": False}}

    subject = _decode(_header(msg, "Subject"))
    from_header = _decode(_header(msg, "From"))
    reply_to = _decode(_header(msg, "Reply-To"))
    display_name, real_from = parseaddr(from_header)

    spf_ok, dkim_ok, dmarc_ok = _auth_result(msg)
    if not spf_ok:
        add("spf_fail", "email_auth", "SPF authentication failed",
            "The email failed SPF authentication and may not come from the claimed domain.",
            "high", _header(msg, "Authentication-Results", "")[:200], 0.85)
    if not dkim_ok:
        add("dkim_fail", "email_auth", "DKIM authentication failed",
            "The email failed DKIM verification.", "high", None, 0.8)
    if not dmarc_ok:
        add("dmarc_fail", "email_auth", "DMARC authentication failed",
            "The email failed DMARC policy checks.", "high", None, 0.75)

    if reply_to and real_from:
        rt_addr = parseaddr(reply_to)[1]
        if rt_addr and rt_addr.lower() != real_from.lower():
            add("reply_to_spoof", "email_auth", "Reply-To mismatch",
                "Replies go to a different address than the sender.",
                "high", f"From: {real_from} / Reply-To: {rt_addr}", 0.9)

    if _sender_spoofed(display_name, from_header, reply_to):
        add("sender_spoofing", "impersonation", "Sender name spoofing",
            "The displayed sender name does not match the real sender address.",
            "critical", f"'{display_name}' <{real_from}>", 0.9)

    if not real_from or not real_from.startswith(("noreply", "no-reply", "notification")):
        if not re.search(r"\.(com|org|net|gov|edu|io|co\.uk|de|fr|nl)$", real_from.split("@")[-1] if "@" in real_from else ""):
            add("unknown_sender", "email_auth", "Unknown sender",
                "The email comes from a domain you may not know.", "medium", real_from, 0.5)

    # --- Body ---------------------------------------------------------------
    body_parts = []
    for part in msg.walk():
        if part.get_content_type() == "text/plain":
            body_parts.append(part.get_content())
        elif part.get_content_type() == "text/html":
            html_body = part.get_content() or ""
            body_parts.append(re.sub(r"<[^>]+>", " ", html_body))
    body = "\n".join(p for p in body_parts if p)
    if not body:
        body = raw[:5000]

    # Run the text scanner against the body.
    from app.services.text_scanner import _scan_text_sync

    text_result = _scan_text_sync(body)
    findings.extend(text_result["findings"])

    # --- Links --------------------------------------------------------------
    links = _extract_links(body)
    suspicious_links = []
    for link in links[:10]:
        short, host = is_shortened(link)
        brand, sim = detect_typosquatting((link.split("/")[2] if "//" in link else "").lower())
        if short or brand or "secure" in link.lower():
            suspicious_links.append(link[:200])
    if suspicious_links:
        add("email_link_suspicious", "email_auth", "Suspicious link in email",
            "The email contains links that look suspicious.",
            "high", "; ".join(suspicious_links[:3]), 0.85)

    # --- Attachments --------------------------------------------------------
    attachments = _extract_attachments(msg)
    dangerous_types = (
        ".exe", ".scr", ".bat", ".cmd", ".vbs", ".ps1", ".js", ".jar",
        ".apk", ".msi", ".reg", ".hta", ".docm", ".xlsm",
    )
    dangerous = [a for a in attachments if a["filename"].lower().endswith(dangerous_types)]
    if dangerous:
        add("email_attachment_suspicious", "email_auth", "Suspicious attachment",
            "The email carries an attachment type commonly used to spread malware.",
            "high", "; ".join(a["filename"] for a in dangerous[:3]), 0.9)

    return {
        "findings": findings,
        "meta": {
            "parsed": True,
            "subject": subject[:300],
            "from": from_header[:300],
            "reply_to": reply_to[:200],
            "spf_ok": spf_ok, "dkim_ok": dkim_ok, "dmarc_ok": dmarc_ok,
            "link_count": len(links),
            "attachment_count": len(attachments),
        },
    }
