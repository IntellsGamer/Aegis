"""Regression coverage for SSRF-safe acquisition and truthful public map data."""
from __future__ import annotations

import pytest

from app.database import SessionLocal
from app.models import ThreatReport
from app.repositories.admin_repo import ThreatReportRepository
from app.security.safe_url import UnsafeDestination, validate_public_url
from app.services.url_scanner import _scan_url_sync
from app.services.geo_service import website_origin


def test_known_website_origins_are_destination_evidence_not_reporter_geography():
    assert website_origin("https://www.google.com/search?q=aegis")["country"] == "US"
    assert website_origin("https://example.com/assessment")["country"] == "US"
    # A lookalike never inherits the real operator’s country assertion.
    assert website_origin("https://google-login.example/") == {}


def test_safe_url_rejects_private_and_non_web_destinations():
    for target in (
        "http://127.0.0.1/",
        "http://169.254.169.254/latest/meta-data/",
        "http://[::1]/",
        "file:///etc/passwd",
    ):
        with pytest.raises(UnsafeDestination):
            validate_public_url(target)


def test_url_scanner_blocks_private_target_before_network_access():
    result = _scan_url_sync("http://127.0.0.1:8000/admin")

    assert result["meta"]["network_fetch"] == "blocked"
    assert result["meta"]["status_code"] == 0
    assert result["findings"][0]["code"] == "unsafe_destination"
    assert result["findings"][0]["extra"]["source"] == "safe_fetch"


def test_url_feedback_uses_destination_origin_over_development_reporter_country(client, monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "environment", "development")
    monkeypatch.setattr(settings, "development_report_country", "IR")
    client.post("/api/v1/auth/register", json={
        "username": "originmapuser", "email": "originmap@example.com", "password": "Str0ngPass!"
    })
    assert client.post("/api/v1/auth/login", json={
        "identifier": "originmap@example.com", "password": "Str0ngPass!"
    }).status_code == 200
    scan = client.post("/api/v1/scans/url", json={"url": "https://example.com"}).get_json()
    # Acquisition context still reflects the local development session.
    assert scan["country"] == "IR"
    feedback = client.post(
        f"/api/v1/scans/{scan['scan_id']}/feedback",
        json={"verdict": "confirmed_malicious"},
    ).get_json()
    assert feedback["triage_report"]["country"] == "US"
    assert feedback["triage_report"]["development_demo_location"] is False


def test_map_excludes_pending_and_returns_approved_country_aggregate(client):
    db = SessionLocal()
    try:
        reports = ThreatReportRepository(db)
        reports.create({
            "content_type": "url", "content": "https://pending.example/", "category": "phishing",
            "country": "IR", "country_name": "Iran", "status": "pending",
            "latitude": 35.0, "longitude": 51.0,
        })
        reports.create({
            "content_type": "url", "content": "https://approved.example/", "category": "phishing",
            "country": "IR", "country_name": "Iran", "status": "approved",
            # Stored precise coordinates must not appear in public payloads.
            "latitude": 35.6892, "longitude": 51.3890,
        })
        db.commit()

        response = client.get("/api/v1/threats/map?range=1")
        assert response.status_code == 200
        body = response.get_json()
        assert body["data_state"] == "verified_approved_reports"
        assert body["location_precision"] == "country_aggregate"
        assert body["total_reports"] == 1
        assert len(body["points"]) == 1
        point = body["points"][0]
        assert point["country_code"] == "IR"
        assert point["provenance"] == "approved_community_report"
        assert point["location_precision"] == "country_aggregate"
        assert point["count"] == 1
        assert (point["lat"], point["lng"]) != (35.6892, 51.3890)
    finally:
        db.query(ThreatReport).filter(
            ThreatReport.content.in_({"https://pending.example/", "https://approved.example/"})
        ).delete(synchronize_session=False)
        db.commit()
        db.close()


def test_map_rejects_unbounded_range(client):
    response = client.get("/api/v1/threats/map?range=365")
    assert response.status_code == 422


def test_private_target_is_a_critical_full_pipeline_verdict(client):
    response = client.post("/api/v1/scans/url", json={"url": "http://127.0.0.1/"})
    assert response.status_code == 200
    body = response.get_json()
    assert body["verdict"] == "threat"
    assert body["trust_score"] <= 25
    assert body["retention"] == "not_stored"


def test_unresolvable_hostname_is_a_limited_assessment_not_a_threat(client):
    response = client.post("/api/v1/scans/url", json={"url": "https://unresolvable-aegis-test.invalid/login"})
    assert response.status_code == 200
    body = response.get_json()
    assert body["assessment_state"] == "limited"
    assert body["verdict"] == "unverified"
    assert body["retention"] == "not_stored"
    codes = {finding["code"] for finding in body["findings"]}
    assert "destination_unresolved" in codes
    assert "suspicious_keywords_url" in codes
