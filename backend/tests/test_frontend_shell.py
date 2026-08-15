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


def test_account_entry_templates_bind_complete_persian_copy():
    catalog = (STATIC_ROOT / "js" / "i18n.js").read_text(encoding="utf-8")
    required_keys = (
        "auth.login_title", "auth.login_intro", "auth.evidence_first", "auth.password_login_placeholder",
        "auth.register_title", "auth.register_intro", "auth.one_flow", "auth.username_placeholder",
        "auth.password_note", "auth.password_repeat_placeholder",
    )
    for template_name in ("login.html", "register.html"):
        template = (TEMPLATE_ROOT / template_name).read_text(encoding="utf-8")
        assert 'data-i18n="auth.' in template
        assert "data-i18n-placeholder" in template
    for key in required_keys:
        assert f"'{key}':" in catalog


def test_static_assets_are_cacheable_and_skip_application_cookie_setup(client):
    response = client.get("/static/js/app.js")

    assert response.status_code == 200
    assert "max-age=" in response.headers.get("Cache-Control", "")
    assert "Set-Cookie" not in response.headers


def test_theme_preference_uses_account_scoped_browser_storage():
    base_template = (TEMPLATE_ROOT / "base.html").read_text(encoding="utf-8")
    app_script = (STATIC_ROOT / "js" / "app.js").read_text(encoding="utf-8")

    assert 'data-theme-storage-key="{{ \'aegis-theme-\' ~ user.id if user else \'aegis-theme\' }}"' in base_template
    assert "localStorage.getItem(storageKey)" in base_template
    assert "function themeStorageKey()" in app_script
    assert "localStorage.setItem(themeStorageKey(), resolvedTheme)" in app_script
    assert "api('PATCH', '/api/v1/users/me', { theme: resolvedTheme })" in app_script


def test_rate_limiter_does_not_charge_safe_scan_navigation_requests():
    application_source = (REPOSITORY_ROOT / "backend" / "app" / "__init__.py").read_text(encoding="utf-8")

    assert 'request.path.startswith("/api/v1/scans") and request.method not in {"GET", "HEAD", "OPTIONS"}' in application_source
    assert 'request.path.startswith("/api/v1/auth") and request.method not in {"GET", "HEAD", "OPTIONS"}' in application_source
    assert "SharedDataMiddleware" in application_source


def test_authenticated_theme_preference_survives_a_server_render(client):
    client.post(
        "/api/v1/auth/register",
        json={"username": "theme_user", "email": "theme@example.com", "password": "Str0ngPass!"},
    )
    client.post(
        "/api/v1/auth/login",
        json={"identifier": "theme@example.com", "password": "Str0ngPass!"},
    )

    update = client.patch("/api/v1/users/me", json={"theme": "light"})
    assert update.status_code == 200
    assert update.get_json()["theme"] == "light"

    dashboard = client.get("/dashboard")
    assert dashboard.status_code == 200
    assert 'data-theme-preference="light"' in dashboard.get_data(as_text=True)
