"""Quick smoke test: pages render and core APIs respond (no external calls)."""
import os

# The smoke test owns this disposable local database. Removing it makes repeated
# runs deterministic on Windows as well as POSIX shells.
try:
    os.remove("smoke_test.db")
except FileNotFoundError:
    pass

os.environ["AEGIS_ENVIRONMENT"] = "test"
os.environ["AEGIS_DATABASE_URL"] = "sqlite:///./smoke_test.db"
# OCR is optional and can require a system binary. Keep the cross-platform
# core smoke path independent from a native Tesseract installation.
os.environ["AEGIS_OCR_ENGINE"] = "none"
os.environ["AEGIS_EMAIL_ENABLED"] = "false"
os.environ["AEGIS_SEED_ON_STARTUP"] = "false"

import sys
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app

app = create_app()
app.config["TESTING"] = True
app.config["WTF_CSRF_ENABLED"] = False

client = app.test_client()

failures = 0

def check(method, path, expected=200, follow=False):
    global failures
    resp = client.open(path, method=method, json={"email": "x@x.com", "password": "bad"})
    if resp.status_code != expected:
        failures += 1
        print(f"FAIL {method} {path} => {resp.status_code} (expected {expected})")
    else:
        print(f"OK   {method} {path} => {resp.status_code}")

# Public pages
for path in ["/", "/login", "/register", "/forgot", "/reset"]:
    resp = client.get(path)
    status = resp.status_code
    ok = status == 200
    if not ok:
        failures += 1
    print(f"{'OK ' if ok else 'FAIL'} GET {path} => {status}")

# Redirects when not logged in
for path in ["/dashboard", "/learn", "/profile", "/search"]:
    resp = client.get(path)
    ok = resp.status_code == 302 and "/login" in resp.headers.get("Location", "")
    if not ok:
        failures += 1
    print(f"{'OK ' if ok else 'FAIL'} GET {path} (anon) => {resp.status_code} -> {resp.headers.get('Location', '')}")
# /scan and /map are public pages
for path in ["/scan", "/map"]:
    resp = client.get(path)
    if resp.status_code != 200:
        failures += 1
    print(f"{'OK ' if resp.status_code == 200 else 'FAIL'} GET {path} (public) => {resp.status_code}")
# admin requires admin
resp = client.get("/admin")
if resp.status_code != 302:
    failures += 1
print(f"{'OK ' if resp.status_code == 302 else 'FAIL'} GET /admin (anon) => {resp.status_code}")

# Public API endpoints
check("GET", "/api/v1/health")
resp = client.post("/api/v1/auth/login", json={"identifier": "x@x.com", "password": "bad"})
if resp.status_code not in (401, 403):
    failures += 1
print(f"{'OK ' if resp.status_code in (401, 403) else 'FAIL'} POST /api/v1/auth/login (bad creds) => {resp.status_code}")
resp = client.get("/api/v1/analytics/summary")
if resp.status_code != 401:
    failures += 1
print(f"{'OK ' if resp.status_code == 401 else 'FAIL'} GET /api/v1/analytics/summary (anon) => {resp.status_code}")

# Full auth + scan flow
resp = client.post("/api/v1/auth/register", json={
    "username": "smoketest", "email": "smoke@example.com", "password": "StrongPass1",
})
print("register:", resp.status_code)
resp = client.post("/api/v1/auth/login", json={
    "identifier": "smoke@example.com", "password": "StrongPass1",
})
print("login:", resp.status_code)

if resp.status_code == 200:
    for path in ["/dashboard", "/scan", "/map", "/learn", "/profile", "/search"]:
        r = client.get(path)
        print(f"page {path}: {r.status_code}")
        if r.status_code != 200:
            failures += 1
    print("analytics summary:", client.get("/api/v1/analytics/summary").status_code)
    print("scans list:", client.get("/api/v1/scans").status_code)
    print("learning lessons:", client.get("/api/v1/learning/lessons").status_code)
    print("learning quizzes:", client.get("/api/v1/learning/quizzes").status_code)
    print("learning simulator:", client.get("/api/v1/learning/simulator").status_code)
    print("learning progress:", client.get("/api/v1/learning/progress").status_code)

# Seeded admin
resp = client.post("/api/v1/auth/login", json={
    "identifier": "admin@aegis.local", "password": "Admin@2024!",
})
print("admin login:", resp.status_code)
if resp.status_code == 200:
    for path in ["/admin",
                 "/api/v1/admin/stats", "/api/v1/admin/threats", "/api/v1/admin/rules",
                 "/api/v1/admin/keywords", "/api/v1/admin/users", "/api/v1/admin/logs",
                 "/api/v1/admin/triage", "/api/v1/admin/conformance", "/api/v1/admin/readiness"]:
        r = client.get(path)
        print(f"admin {path}: {r.status_code}")
        if r.status_code != 200:
            failures += 1

# Anonymous URL scan (text scan hits no external network)
resp = client.post("/api/v1/scans/text", json={"text": "URGENT: your account will be locked unless you click http://paypa1-login.example to verify immediately."})
print("anon text scan:", resp.status_code)
if resp.status_code == 200:
    data = resp.get_json()
    print("  scan id:", data.get("scan_id"), "verdict:", data.get("verdict"), "score:", data.get("trust_score"))
    scan_id = data["scan_id"]
    print("  get scan:", client.get(f"/api/v1/scans/{scan_id}").status_code)
    print("  pdf:", client.get(f"/api/v1/scans/{scan_id}/report.pdf").status_code)
else:
    failures += 1

print("\nFAILURES:", failures)
sys.exit(1 if failures else 0)
