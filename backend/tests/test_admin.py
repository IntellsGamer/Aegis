"""Admin API tests: role enforcement and stats endpoints."""
ADMIN = {"identifier": "admin@aegis.local", "password": "Admin@2024!"}


def test_admin_endpoints_require_auth(client):
    assert client.get("/api/v1/admin/stats").status_code == 401


def test_admin_endpoints_forbid_non_admin(client):
    client.post("/api/v1/auth/register",
                json={"username": "grace", "email": "grace@example.com", "password": "Str0ngPass!"})
    resp = client.post("/api/v1/auth/login",
                       json={"identifier": "grace@example.com", "password": "Str0ngPass!"})
    assert resp.status_code == 200
    token = resp.get_json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    assert client.get("/api/v1/admin/stats", headers=headers).status_code == 403
    assert client.get("/api/v1/admin/users", headers=headers).status_code == 403


def test_admin_stats(client):
    client.post("/api/v1/auth/login", json=ADMIN)
    resp = client.get("/api/v1/admin/stats")
    assert resp.status_code == 200
    body = resp.get_json()
    assert "totals" in body and "recent_scans" in body


def test_admin_endpoints(client):
    client.post("/api/v1/auth/login", json=ADMIN)
    for path in ["/api/v1/admin/threats", "/api/v1/admin/rules",
                 "/api/v1/admin/keywords", "/api/v1/admin/users", "/api/v1/admin/logs"]:
        assert client.get(path).status_code == 200, path
