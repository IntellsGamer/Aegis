"""Operational triage, conformance, and matcher-precision regressions."""
from __future__ import annotations

from app.ai.link_analysis import analyze_embedded_url

ADMIN = {"identifier": "admin@aegis.local", "password": "Admin@2024!"}


def test_benign_subdomain_does_not_become_a_brand_lookalike():
    findings, _ = analyze_embedded_url("https://library.example.org/hours")
    assert "typosquatting" not in {finding["code"] for finding in findings}


def test_admin_triage_requires_authentication(client):
    assert client.get("/api/v1/admin/triage").status_code == 401
    assert client.get("/api/v1/admin/conformance").status_code == 401


def test_admin_conformance_reports_fixed_fictional_contracts(client):
    client.post("/api/v1/auth/login", json=ADMIN)
    response = client.get("/api/v1/admin/conformance")
    assert response.status_code == 200
    body = response.get_json()
    assert body["kind"] == "deterministic conformance"
    assert body["summary"] == {"total": 3, "passed": 3, "failed": 0}
    assert all(case["passed"] for case in body["cases"])
    assert "not a benchmark" in body["purpose"]


def test_admin_triage_excludes_safety_boundary_only_blocks(client):
    client.post("/api/v1/auth/login", json=ADMIN)
    blocked = client.post("/api/v1/scans/url", json={"url": "http://127.0.0.1:8000/admin"})
    assert blocked.status_code == 200
    response = client.get("/api/v1/admin/triage?limit=20")
    assert response.status_code == 200
    assert blocked.get_json()["scan_id"] not in {item["scan_id"] for item in response.get_json()["items"]}


def test_admin_triage_includes_persisted_high_risk_scan_and_review_state(client):
    client.post("/api/v1/auth/login", json=ADMIN)
    scan = client.post("/api/v1/scans/text", json={
        "text": "Urgent fictional fixture: verify at https://paypa1-account-review.example/verify?account=demo"
    })
    assert scan.status_code == 200

    response = client.get("/api/v1/admin/triage?limit=5")
    assert response.status_code == 200
    body = response.get_json()
    item = next(row for row in body["items"] if row["scan_id"] == scan.get_json()["scan_id"])
    assert item["review"]["state"] == "awaiting_review"
    assert item["strongest_evidence"]
    assert any(family["name"] == "impersonation" for family in item["evidence_families"])
