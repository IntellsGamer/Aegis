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


def test_admin_triage_exposes_pending_linked_community_report(client):
    client.post("/api/v1/auth/register", json={
        "username": "triagereportuser", "email": "triagereport@example.com", "password": "Str0ngPass!"
    })
    assert client.post("/api/v1/auth/login", json={
        "identifier": "triagereport@example.com", "password": "Str0ngPass!"
    }).status_code == 200
    scan = client.post(
        "/api/v1/scans/text",
        json={"text": "A user-confirmed malicious report for triage metadata coverage."},
        headers={"cf-ipcountry": "IR"},
    ).get_json()
    feedback = client.post(
        f"/api/v1/scans/{scan['scan_id']}/feedback",
        json={"verdict": "confirmed_malicious"},
    ).get_json()

    assert client.post("/api/v1/auth/login", json=ADMIN).status_code == 200
    triage = client.get("/api/v1/admin/triage?limit=25").get_json()
    item = next(row for row in triage["items"] if row["scan_id"] == scan["scan_id"])
    assert item["community_report"]["id"] == feedback["triage_report"]["id"]
    assert item["community_report"]["status"] == "pending"
    assert item["community_report"]["country"] == "IR"
    assert item["community_report"]["map_eligible"] is True


def test_triage_repairs_legacy_local_pending_report_in_development(client, monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "environment", "test")
    client.post("/api/v1/auth/register", json={
        "username": "legacyreportuser", "email": "legacyreport@example.com", "password": "Str0ngPass!"
    })
    assert client.post("/api/v1/auth/login", json={
        "identifier": "legacyreport@example.com", "password": "Str0ngPass!"
    }).status_code == 200
    scan = client.post("/api/v1/scans/text", json={"text": "Legacy localhost assessment."}).get_json()
    assert scan["country"] is None
    feedback = client.post(
        f"/api/v1/scans/{scan['scan_id']}/feedback",
        json={"verdict": "confirmed_malicious"},
    ).get_json()
    assert feedback["triage_report"]["map_eligible_after_approval"] is False

    monkeypatch.setattr(settings, "environment", "development")
    monkeypatch.setattr(settings, "development_report_country", "IR")
    assert client.post("/api/v1/auth/login", json=ADMIN).status_code == 200
    triage = client.get("/api/v1/admin/triage?limit=25").get_json()
    item = next(row for row in triage["items"] if row["scan_id"] == scan["scan_id"])
    assert item["community_report"]["country"] == "IR"
    assert item["community_report"]["map_eligible"] is True
