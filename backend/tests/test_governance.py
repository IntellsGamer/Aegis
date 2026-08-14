"""Tests for governed threat intelligence and measured analyst outcomes."""
from __future__ import annotations

ADMIN = {"identifier": "admin@aegis.local", "password": "Admin@2024!"}


def _login_admin(client):
    response = client.post("/api/v1/auth/login", json=ADMIN)
    assert response.status_code == 200


def test_feed_catalog_is_visible_and_remote_terms_are_enforced(client):
    _login_admin(client)
    response = client.get("/api/v1/admin/feeds")
    assert response.status_code == 200
    feeds = {feed["slug"]: feed for feed in response.get_json()}
    assert {"local", "urlhaus", "openphish", "phishtank"}.issubset(feeds)
    assert feeds["local"]["enabled"] is True
    assert feeds["urlhaus"]["enabled"] is False

    denied = client.patch("/api/v1/admin/feeds/urlhaus", json={"enabled": True, "terms_accepted": False})
    assert denied.status_code == 422


def test_local_feed_import_records_provenance(client):
    _login_admin(client)
    response = client.post("/api/v1/admin/feeds/local/indicators", json={
        "indicators": [{
            "threat_type": "domain", "value": "verified-test-indicator.example",
            "category": "phishing", "severity": "high", "confidence": 0.96,
            "source_reference": "internal case AEGIS-TEST-1",
        }]
    })
    assert response.status_code == 201
    assert response.get_json()["ingested"] == 1

    threats = client.get("/api/v1/admin/threats").get_json()["items"]
    imported = next(item for item in threats if item["value"] == "verified-test-indicator.example")
    assert imported["source"] == "feed:local"


def test_analyst_outcome_is_recorded_separately_from_engine_confidence(client):
    _login_admin(client)
    scan_response = client.post("/api/v1/scans/text", json={
        "text": "Urgent: verify your account at http://paypa1-login.example now."
    })
    assert scan_response.status_code == 200
    scan_id = scan_response.get_json()["scan_id"]

    outcome = client.post(f"/api/v1/admin/scans/{scan_id}/outcome", json={
        "verdict": "confirmed_malicious", "rationale": "Verified by analyst test case."
    })
    assert outcome.status_code == 201
    assert outcome.get_json()["verdict"] == "confirmed_malicious"

    summary = client.get("/api/v1/admin/outcomes?days=30")
    assert summary.status_code == 200
    assert summary.get_json()["by_verdict"]["confirmed_malicious"] >= 1


def test_incident_packet_preserves_evidence_and_response_context(client):
    _login_admin(client)
    scan_response = client.post("/api/v1/scans/text", json={
        "text": "URGENT: Click http://paypa1-login.example to confirm your bank account now."
    })
    assert scan_response.status_code == 200
    scan_id = scan_response.get_json()["scan_id"]

    packet = client.get(f"/api/v1/scans/{scan_id}/incident-packet")
    assert packet.status_code == 200
    body = packet.get_json()
    assert body["case_id"] == f"AEGIS-{scan_id}"
    assert body["classification"]["engine"] == "evidence-fusion-v2"
    assert "not measured predictive accuracy" in body["classification"]["interpretation"]
    assert body["evidence"]
    assert body["containment_actions"]


def test_scan_owner_can_record_outcome_feedback(client):
    client.post("/api/v1/auth/register", json={
        "username": "feedbackuser", "email": "feedback@example.com", "password": "Str0ngPass!"
    })
    assert client.post("/api/v1/auth/login", json={
        "identifier": "feedback@example.com", "password": "Str0ngPass!"
    }).status_code == 200
    scan = client.post("/api/v1/scans/text", json={
        "text": "Urgent: verify your account at http://paypa1-login.example now."
    }).get_json()
    assert scan["scan_id"]

    feedback = client.post(f"/api/v1/scans/{scan['scan_id']}/feedback", json={"verdict": "confirmed_malicious"})
    assert feedback.status_code == 201
    assert feedback.get_json()["verdict"] == "confirmed_malicious"
