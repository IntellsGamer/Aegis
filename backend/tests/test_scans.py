"""Scan API tests: anonymous text scan, retrieval, PDF, history."""
PHISH = ("URGENT: your account will be locked unless you click "
         "http://paypa1-login.example to verify immediately.")


def test_anonymous_text_scan_is_not_retained_without_consent(client):
    resp = client.post("/api/v1/scans/text", json={"text": PHISH})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["scan_id"] is None
    assert data["retention"] == "not_stored"
    assert data["verdict"] == "threat"
    assert data["trust_score"] < 50
    assert isinstance(data["findings"], list) and data["findings"]
    assert data["reasons"]


def test_text_scan_validation(client):
    resp = client.post("/api/v1/scans/text", json={})
    assert resp.status_code == 422
    resp = client.post("/api/v1/scans/text", json={"text": ""})
    assert resp.status_code == 422


def test_get_scan_and_pdf(client):
    client.post("/api/v1/auth/register",
                json={"username": "frank", "email": "frank@example.com", "password": "Str0ngPass!"})
    client.post("/api/v1/auth/login",
                json={"identifier": "frank@example.com", "password": "Str0ngPass!"})
    data = client.post("/api/v1/scans/text", json={"text": PHISH}).get_json()
    scan_id = data["scan_id"]
    resp = client.get(f"/api/v1/scans/{scan_id}")
    assert resp.status_code == 200
    assert resp.get_json()["scan_id"] == scan_id

    pdf = client.get(f"/api/v1/scans/{scan_id}/report.pdf")
    assert pdf.status_code == 200
    assert pdf.data.startswith(b"%PDF")


def test_scans_history_requires_auth(client):
    assert client.get("/api/v1/scans").status_code == 401


def test_scans_history_after_login(client):
    client.post("/api/v1/auth/register",
                json={"username": "frank", "email": "frank@example.com", "password": "Str0ngPass!"})
    client.post("/api/v1/auth/login",
                json={"identifier": "frank@example.com", "password": "Str0ngPass!"})
    resp = client.get("/api/v1/scans")
    assert resp.status_code == 200
    body = resp.get_json()
    assert "items" in body and "total" in body
