"""Competition-readiness regressions for reviewable casefiles and governance."""
from __future__ import annotations

ADMIN = {"identifier": "admin@aegis.local", "password": "Admin@2024!"}


def test_casefile_packages_persisted_evidence_with_integrity_fingerprint(client):
    client.post("/api/v1/auth/register", json={
        "username": "caseowner", "email": "caseowner@example.com", "password": "Str0ngPass!"
    })
    scan = client.post("/api/v1/scans/text", json={
        "text": "Urgent account verification is required at http://paypa1-login.example/verify"
    }).get_json()
    assert scan["scan_id"]

    response = client.get(f"/api/v1/scans/{scan['scan_id']}/casefile")
    assert response.status_code == 200
    body = response.get_json()
    assert body["case_id"] == f"AEGIS-{scan['scan_id']}"
    assert body["classification"]["engine"] == "evidence-fusion-v2"
    assert body["integrity"]["algorithm"] == "SHA-256"
    assert len(body["integrity"]["fingerprint"]) == 64
    assert body["provenance"]["training_boundary"].startswith("No model training")
    assert body["provenance"]["network_acquisition"] == "not_applicable"
    assert body["evidence"]
    assert body["limitations"]


def test_casefile_is_not_exposed_to_an_unrelated_user(client):
    client.post("/api/v1/auth/register", json={
        "username": "ownercase", "email": "ownercase@example.com", "password": "Str0ngPass!"
    })
    scan = client.post("/api/v1/scans/text", json={"text": "please verify your account urgently"}).get_json()
    client.post("/api/v1/auth/logout")
    client.post("/api/v1/auth/register", json={
        "username": "othercase", "email": "othercase@example.com", "password": "Str0ngPass!"
    })
    assert client.get(f"/api/v1/scans/{scan['scan_id']}/casefile").status_code == 404


def test_readiness_endpoint_discloses_governance_without_claiming_accuracy(client):
    assert client.get("/api/v1/admin/readiness").status_code == 401
    client.post("/api/v1/auth/login", json=ADMIN)
    response = client.get("/api/v1/admin/readiness")
    assert response.status_code == 200
    body = response.get_json()
    assert body["engine"]["training_required"] is False
    assert body["engine"]["llm_used"] is False
    assert body["feeds"]
    assert "not a claim of measured accuracy" in body["measurement_note"]
    assert any(item["control"] == "No training boundary" for item in body["safeguards"])
