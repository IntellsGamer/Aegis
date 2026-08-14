"""Non-executing upload safety regressions."""
from __future__ import annotations

from io import BytesIO

import pytest

from app.security.file_safety import UnsafeUpload, inspect_upload
from app.services.file_scanner import _scan_file_sync


def test_pdf_magic_mismatch_is_rejected():
    with pytest.raises(UnsafeUpload):
        inspect_upload(b"MZ\x90\x00not-a-pdf", "invoice.pdf", "file")


def test_static_pdf_actions_are_reported_without_execution(tmp_path):
    path = tmp_path / "invoice.pdf"
    path.write_bytes(b"%PDF-1.7\n1 0 obj << /OpenAction 2 0 R /JavaScript (app.alert('x')) >>\n%%EOF")

    result = _scan_file_sync(str(path), "invoice.pdf", "application/pdf")
    codes = {finding["code"] for finding in result["findings"]}
    assert "pdf_javascript" in codes
    assert "pdf_open_action" in codes
    assert result["meta"]["file_safety"] == "static_inspection_complete"


def test_file_endpoint_rejects_renamed_binary(client):
    response = client.post(
        "/api/v1/scans/file",
        data={"file": (BytesIO(b"MZ\x90\x00fake-executable"), "invoice.pdf")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 422
    assert "does not contain a PDF signature" in response.get_json()["detail"]


def test_msg_requires_compound_document_signature():
    with pytest.raises(UnsafeUpload):
        inspect_upload(b"From: attacker@example.invalid", "message.msg", "file")
