"""Auth API tests: register, login, session, password reset."""
import pytest


def test_health(client):
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ok"


def test_register_and_login(client):
    data = {"username": "alice", "email": "alice@example.com", "password": "Str0ngPass!"}
    resp = client.post("/api/v1/auth/register", json=data)
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["access_token"] and body["refresh_token"]
    assert body["user_id"] > 0

    resp = client.post("/api/v1/auth/login",
                       json={"identifier": "alice@example.com", "password": "Str0ngPass!"})
    assert resp.status_code == 200
    assert resp.get_json()["user_id"] == body["user_id"]


def test_register_duplicate_email(client):
    data = {"username": "bob", "email": "bob@example.com", "password": "Str0ngPass!"}
    assert client.post("/api/v1/auth/register", json=data).status_code == 200
    resp = client.post("/api/v1/auth/register", json=data)
    assert resp.status_code == 409


def test_login_bad_credentials(client):
    resp = client.post("/api/v1/auth/login",
                       json={"identifier": "admin@aegis.local", "password": "wrong"})
    assert resp.status_code == 401


def test_me_requires_auth(client):
    assert client.get("/api/v1/auth/me").status_code == 401
    resp = client.post("/api/v1/auth/login",
                       json={"identifier": "admin@aegis.local", "password": "Admin@2024!"})
    token = resp.get_json()["access_token"]
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.get_json()["is_admin"] is True


def test_password_reset_flow(client):
    data = {"username": "carol", "email": "carol@example.com", "password": "Str0ngPass!"}
    assert client.post("/api/v1/auth/register", json=data).status_code == 200

    resp = client.post("/api/v1/auth/forgot-password", json={"email": "carol@example.com"})
    assert resp.status_code == 200
    token = resp.get_json()["token"]
    assert token

    resp = client.post("/api/v1/auth/reset-password",
                       json={"token": token, "new_password": "NewPass123!"})
    assert resp.status_code == 200

    resp = client.post("/api/v1/auth/login",
                       json={"identifier": "carol@example.com", "password": "NewPass123!"})
    assert resp.status_code == 200


def test_logout(client):
    client.post("/api/v1/auth/register",
                json={"username": "dave", "email": "dave@example.com", "password": "Str0ngPass!"})
    client.post("/api/v1/auth/login",
                json={"identifier": "dave@example.com", "password": "Str0ngPass!"})
    assert client.get("/api/v1/auth/me").status_code == 200
    assert client.post("/api/v1/auth/logout").status_code == 200
    assert client.get("/api/v1/auth/me").status_code == 401
