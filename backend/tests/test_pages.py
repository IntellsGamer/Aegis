"""Page rendering tests: public pages, redirects, authenticated pages."""
import pytest


PUBLIC = ["/", "/login", "/register", "/forgot", "/reset", "/scan", "/map"]
AUTH_ONLY = ["/dashboard", "/learn", "/profile", "/search"]


@pytest.mark.parametrize("path", PUBLIC)
def test_public_pages(client, path):
    assert client.get(path).status_code == 200


@pytest.mark.parametrize("path", AUTH_ONLY)
def test_auth_pages_redirect_anon(client, path):
    resp = client.get(path)
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


@pytest.mark.parametrize("path", AUTH_ONLY)
def test_auth_pages_after_login(client, path):
    client.post("/api/v1/auth/register",
                json={"username": "erin", "email": "erin@example.com", "password": "Str0ngPass!"})
    client.post("/api/v1/auth/login",
                json={"identifier": "erin@example.com", "password": "Str0ngPass!"})
    assert client.get(path).status_code == 200


def test_admin_page_redirects_anon(client):
    resp = client.get("/admin")
    assert resp.status_code == 302


def test_admin_page_after_admin_login(client):
    client.post("/api/v1/auth/login",
                json={"identifier": "admin@aegis.local", "password": "Admin@2024!"})
    assert client.get("/admin").status_code == 200
