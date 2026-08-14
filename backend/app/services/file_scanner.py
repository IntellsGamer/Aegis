"""File scanner: extract text from PDFs and text files, then analyze content."""
from __future__ import annotations

import asyncio
import os
import re
from pathlib import Path

from app.ai.text_patterns import URL_RE
from app.security.file_safety import UnsafeUpload, inspect_upload


async def scan_file(file_path: str, filename: str, mime: str | None = None) -> dict:
    return await asyncio.to_thread(_scan_file_sync, file_path, filename, mime)


def _extract_pdf(path: str) -> str:
    try:
        from pypdf import PdfReader

        reader = PdfReader(path)
        pages = []
        for page in reader.pages[:40]:
            pages.append(page.extract_text() or "")
        return "\n".join(pages)
    except Exception:
        try:
            import PyPDF2

            reader = PyPDF2.PdfReader(path)
            return "\n".join(page.extract_text() or "" for page in reader.pages[:40])
        except Exception:
            return ""


def _extract_text_file(path: str) -> str:
    for encoding in ("utf-8", "latin-1", "utf-16"):
        try:
            with open(path, "r", encoding=encoding) as fh:
                return fh.read(200_000)
        except Exception:
            continue
    return ""


def _scan_file_sync(file_path: str, filename: str, mime: str | None = None) -> dict:
    findings: list[dict] = []
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    try:
        inspection = inspect_upload(Path(file_path).read_bytes(), filename, "file")
        findings.extend(inspection.findings)
    except (OSError, UnsafeUpload) as exc:
        return {
            "findings": [{
                "code": "unsafe_upload", "category": "file_safety", "title": "Unsafe or malformed upload",
                "description": "The file could not be safely validated for analysis.", "evidence": str(exc)[:300],
                "severity": "high", "impact": 0.0, "confidence": 0.95,
            }],
            "meta": {"extracted_chars": 0, "links": [], "suspicious_terms": 1, "file_safety": "blocked"},
        }

    text = ""
    if ext == "pdf" or (mime and "pdf" in mime):
        text = _extract_pdf(file_path)
        if not text:
            findings.append({
                "code": "no_content", "category": "code",
                "title": "No extractable text",
                "description": "No text could be extracted from the PDF (scanned image or protected).",
                "evidence": None, "severity": "medium", "impact": 0.0, "confidence": 0.6,
            })
    elif ext in ("txt", "eml", "msg") or (mime and mime.startswith("text/")):
        text = _extract_text_file(file_path)
    else:
        # Binary file of unknown type - warn
        findings.append({
            "code": "email_attachment_suspicious", "category": "email_auth",
            "title": "Unsupported file type",
            "description": f"Files of type .{ext} cannot be fully analyzed.",
            "evidence": filename, "severity": "medium", "impact": 0.0, "confidence": 0.7,
        })
        return {"findings": findings, "meta": {"extracted_chars": 0, "links": [], "suspicious_terms": 0}}

    from app.services.text_scanner import _scan_text_sync

    if text:
        result = _scan_text_sync(text)
        findings.extend(result["findings"])

    links = URL_RE.findall(text)
    suspicious_terms = len([f for f in findings if f["code"] not in ("no_scam_patterns", "bad_grammar", "ml_scam_probability")])

    return {
        "findings": findings,
        "meta": {
            "extracted_chars": len(text),
            "links": links[:10],
            "link_count": len(links),
            "suspicious_terms": suspicious_terms,
            "file_safety": "static_inspection_complete",
        },
    }
