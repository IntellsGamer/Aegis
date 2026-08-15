"""Regression coverage for the compiled frontend shell and client bootstrap."""
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
STATIC_ROOT = REPOSITORY_ROOT / "backend" / "app" / "static"
TEMPLATE_ROOT = REPOSITORY_ROOT / "backend" / "app" / "templates"


def test_anonymous_shell_has_no_sidebar_or_desktop_sidebar_utility(client):
    response = client.get("/login")
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert 'data-authenticated="false"' in body
    assert 'id="sidebar"' not in body
    assert "lg:ml-64" not in body


def test_authenticated_shell_renders_the_sidebar(client):
    client.post(
        "/api/v1/auth/register",
        json={"username": "shell_user", "email": "shell@example.com", "password": "Str0ngPass!"},
    )
    client.post(
        "/api/v1/auth/login",
        json={"identifier": "shell@example.com", "password": "Str0ngPass!"},
    )
    response = client.get("/dashboard")
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert 'data-authenticated="true"' in body
    assert 'id="sidebar"' in body


def test_frontend_uses_compiled_local_tailwind_and_turbo_assets():
    base_template = (TEMPLATE_ROOT / "base.html").read_text(encoding="utf-8")
    stylesheet = STATIC_ROOT / "css" / "tailwind.css"
    turbo = STATIC_ROOT / "js" / "turbo.js"
    chart = STATIC_ROOT / "js" / "chart.js"
    dashboard_template = (TEMPLATE_ROOT / "dashboard.html").read_text(encoding="utf-8")

    assert "cdn.tailwindcss.com" not in base_template
    assert "js/3.4.17.js" not in base_template
    assert "css/tailwind.css" in base_template
    assert "js/turbo.js" in base_template
    assert stylesheet.is_file() and stylesheet.stat().st_size > 10_000
    assert turbo.is_file() and turbo.stat().st_size > 10_000
    assert chart.is_file() and chart.stat().st_size > 10_000
    assert "cdn.jsdelivr.net" not in dashboard_template
    assert "js/chart.js" in dashboard_template
    assert not (STATIC_ROOT / "js" / "3.4.17.js").exists()


def test_sidebar_offset_and_turbo_lifecycle_guards():
    app_css = (STATIC_ROOT / "css" / "app.css").read_text(encoding="utf-8")
    app_script = (STATIC_ROOT / "js" / "app.js").read_text(encoding="utf-8")
    scan_script = (STATIC_ROOT / "js" / "scan.js").read_text(encoding="utf-8")
    profile_script = (STATIC_ROOT / "js" / "profile.js").read_text(encoding="utf-8")
    dashboard_script = (STATIC_ROOT / "js" / "dashboard.js").read_text(encoding="utf-8")

    assert 'body[data-authenticated="true"] .app-main' in app_css
    assert ".turbo-progress-bar" in app_css
    assert "window.Turbo.config.drive.progressBarDelay = 80" in app_script
    assert "window.Aegis.onPageLoad('scan'" in scan_script
    assert "if (!profileForm.isConnected) return" in profile_script
    assert "Chart.getChart(activity)?.destroy()" in dashboard_script
    assert "Chart.getChart(score)?.destroy()" in dashboard_script


def test_turbo_route_modules_guard_shared_client_bootstrap():
    for module in ("admin.js", "dashboard.js", "learn.js", "map.js", "profile.js", "report.js", "search.js"):
        source = (STATIC_ROOT / "js" / module).read_text(encoding="utf-8")
        assert "const shared = window.Aegis;" in source
        assert "if (!shared)" in source
        assert "aegis:ready" in source
