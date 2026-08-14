"""Non-executing safety checks for untrusted uploads.

These checks run before a file is written to the application's upload area. They
validate the small supported format set against magic bytes and surface static
PDF action indicators. They do not execute, render, unpack, or run macros from
uploaded content.
"""
from __future__ import annotations

from dataclasses import dataclass


class UnsafeUpload(ValueError):
    """The file declaration and its bytes are unsafe or inconsistent."""


@dataclass(frozen=True)
class UploadInspection:
    detected_type: str
    findings: tuple[dict, ...]


_OLE_MAGIC = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"
_PDF_ACTIONS = {
    b"/JavaScript": ("pdf_javascript", "Embedded PDF JavaScript", "critical"),
    b"/JS": ("pdf_javascript", "Embedded PDF JavaScript", "critical"),
    b"/OpenAction": ("pdf_open_action", "Automatic PDF action", "high"),
    b"/Launch": ("pdf_launch_action", "PDF launch action", "critical"),
    b"/EmbeddedFile": ("pdf_embedded_file", "Embedded file in PDF", "high"),
}


def _is_probably_text(content: bytes) -> bool:
    sample = content[:8192]
    if b"\x00" in sample:
        return False
    try:
        sample.decode("utf-8")
        return True
    except UnicodeDecodeError:
        return False


def inspect_upload(content: bytes, filename: str, scan_type: str) -> UploadInspection:
    """Validate content without executing it and return static risk findings."""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if not content:
        raise UnsafeUpload("Empty uploads are not accepted")

    if scan_type in {"image", "qr"}:
        # Pillow and zxing-cpp perform later parsing. Basic image signature
        # validation prevents a renamed executable/text blob from reaching them.
        image_signatures = (b"\x89PNG\r\n\x1a\n", b"\xff\xd8\xff", b"GIF87a", b"GIF89a", b"RIFF", b"BM")
        if not any(content.startswith(signature) for signature in image_signatures):
            raise UnsafeUpload("The uploaded image does not match a supported image signature")
        return UploadInspection("image", ())

    if ext == "pdf":
        if not content.startswith(b"%PDF-"):
            raise UnsafeUpload("The uploaded file is named .pdf but does not contain a PDF signature")
        findings = []
        lower = content.lower()
        for marker, (code, title, severity) in _PDF_ACTIONS.items():
            if marker.lower() in lower:
                findings.append({
                    "code": code, "category": "file_safety", "title": title,
                    "description": "Static inspection found an active PDF construct. The file was not executed.",
                    "evidence": marker.decode("ascii", errors="ignore"), "severity": severity,
                    "impact": 0.0, "confidence": 0.9,
                })
        if b"/Encrypt" in content:
            findings.append({
                "code": "pdf_encrypted", "category": "file_safety", "title": "Encrypted PDF",
                "description": "The PDF is encrypted or password-protected and may not be fully inspectable.",
                "evidence": "/Encrypt", "severity": "medium", "impact": 0.0, "confidence": 0.95,
            })
        return UploadInspection("pdf", tuple(findings))

    if ext == "msg":
        if not content.startswith(_OLE_MAGIC):
            raise UnsafeUpload("The uploaded file is named .msg but does not contain an Outlook MSG signature")
        return UploadInspection("outlook_msg", ())

    if ext in {"txt", "eml"}:
        if not _is_probably_text(content):
            raise UnsafeUpload(f"The uploaded file is named .{ext} but appears to be binary")
        return UploadInspection("text", ())

    raise UnsafeUpload(f"Unsupported upload extension: .{ext or 'unknown'}")
