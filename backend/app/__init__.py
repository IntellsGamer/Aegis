"""Flask application factory and request-lifecycle hooks.

Serves the full-stack app: server-rendered Jinja2 templates + a JSON API,
wrapped with security headers, CSRF protection, rate limiting, structured
logging and per-request database sessions.
"""
from __future__ import annotations

import logging
import secrets
from pathlib import Path

from flask import Flask, g, jsonify, request

from app.config import settings
from app.database import SessionLocal, init_db
from app.exceptions import APIError
from app.utils.logging import clear_context, configure_logging, set_context

BASE_DIR = Path(__file__).resolve().parent

_CSP = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://unpkg.com; "
    "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
    "font-src 'self' https://fonts.gstatic.com data:; "
    "img-src 'self' data: blob: https://*.tile.openstreetmap.org; "
    "connect-src 'self'; "
    "frame-ancestors 'none'; "
    "base-uri 'self'; "
    "form-action 'self'"
)

_SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(self), microphone=(), camera=()",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Strict-Transport-Security": "max-age=63072000; includeSubDomains; preload",
    "Content-Security-Policy": _CSP,
}

# Unsafe-method paths exempt from CSRF (used by API clients with Bearer tokens).
_CSRF_EXEMPT = ("/api/v1/auth/login", "/api/v1/auth/register",
                "/api/v1/auth/refresh", "/api/v1/notifications/stream")


def create_app(config_override: dict | None = None) -> Flask:
    app = Flask(
        __name__,
        template_folder=str(BASE_DIR / "templates"),
        static_folder=str(BASE_DIR / "static"),
    )
    app.config.update(
        SECRET_KEY=settings.secret_key,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=False,  # enable behind TLS
        MAX_CONTENT_LENGTH=settings.max_upload_mb * 1024 * 1024,
        JSON_SORT_KEYS=False,
        DEBUG=settings.debug,
    )
    if config_override:
        app.config.update(config_override)

    configure_logging(settings.environment)

    # --- database lifecycle -------------------------------------------------
    @app.before_request
    def open_db():
        g.db = SessionLocal()
        set_context(trace_id=request.headers.get("X-Trace-Id") or secrets.token_hex(8),
                    path=request.path, method=request.method)

    @app.teardown_request
    def close_db(_exc=None):
        db = g.pop("db", None)
        if db is not None:
            if _exc is None:
                db.commit()
            else:
                db.rollback()
            db.close()
        clear_context()

    # --- security headers ---------------------------------------------------
    @app.after_request
    def security_headers(response):
        for name, value in _SECURITY_HEADERS.items():
            response.headers.setdefault(name, value)
        response.headers.setdefault("X-Trace-Id", request.headers.get("X-Trace-Id", ""))
        return response

    # --- CSRF protection ----------------------------------------------------
    @app.before_request
    def csrf_protection():
        if request.method in ("GET", "HEAD", "OPTIONS", "TRACE"):
            return None
        if app.config.get("TESTING"):
            return None
        if request.path.startswith(_CSRF_EXEMPT):
            return None
        token = request.headers.get("X-CSRF-Token", "")
        expected = request.cookies.get("aegis_csrf") or ""
        if request.headers.get("Authorization", "").startswith("Bearer "):
            return None  # token-authenticated API clients skip CSRF
        if not expected or not token or not secrets.compare_digest(expected, token):
            return jsonify({"detail": "CSRF validation failed"}), 403
        return None

    @app.before_request
    def csrf_token_cookie():
        if "aegis_csrf" not in request.cookies and request.method in ("GET", "HEAD", "OPTIONS"):
            # issued lazily on safe requests so forms have a token available
            pass
        return None

    @app.after_request
    def ensure_csrf_cookie(response):
        if "aegis_csrf" not in request.cookies:
            response.set_cookie(
                "aegis_csrf", secrets.token_urlsafe(32),
                httponly=True, samesite="Lax", secure=False,
            )
        return response

    # --- error handling -------------------------------------------------------
    @app.errorhandler(APIError)
    def handle_api_error(error: APIError):
        response = jsonify({"detail": error.detail})
        response.status_code = error.status_code
        return response

    @app.errorhandler(404)
    def not_found(_e):
        if request.path.startswith("/api/"):
            return jsonify({"detail": "Not found"}), 404
        return app.send_static_file("404.html") if _static_exists(app, "404.html") else ("Not found", 404)

    @app.errorhandler(405)
    def method_not_allowed(_e):
        return jsonify({"detail": "Method not allowed"}), 405

    @app.errorhandler(413)
    def too_large(_e):
        return jsonify({"detail": "Upload exceeds the allowed size"}), 413

    @app.errorhandler(Exception)
    def unhandled(error):
        app.logger.exception("Unhandled error: %s", error)
        return jsonify({"detail": "Internal server error"}), 500

    # --- rate limiting ---------------------------------------------------------
    from app.security.rate_limit import check_rate_limit_sync, client_key

    @app.get("/api/v1/health")
    def health():
        return jsonify({"status": "ok", "version": settings.app_version})

    @app.before_request
    def rate_limit_hook():
        if app.config.get("TESTING"):
            return None
        if request.path.startswith("/api/v1/scans"):
            scope = "scan"
            limit = settings.rate_limit_scan
        elif request.path.startswith("/api/v1/auth"):
            scope = "auth"
            limit = settings.rate_limit_auth
        elif request.path.startswith("/api/v1/admin"):
            scope = "admin"
            limit = settings.rate_limit_admin
        else:
            return None
        result = check_rate_limit_sync(client_key(request, scope), limit)
        if not result.allowed:
            response = jsonify({"detail": "Rate limit exceeded, please slow down."})
            response.status_code = 429
            response.headers["Retry-After"] = str(result.retry_after)
            return response
        return None

    # --- blueprints -------------------------------------------------------------
    from app.routes.auth import bp as auth_bp
    from app.routes.pages import bp as pages_bp
    from app.routes.scans import bp as scans_bp
    from app.routes.users import bp as users_bp
    from app.routes.threats import bp as threats_bp
    from app.routes.learning import bp as learning_bp
    from app.routes.admin import bp as admin_bp
    from app.routes.analytics import bp as analytics_bp
    from app.routes.notifications import bp as notifications_bp
    from app.routes.search import bp as search_bp

    for bp in (pages_bp, auth_bp, scans_bp, users_bp, threats_bp,
               learning_bp, admin_bp, analytics_bp, notifications_bp, search_bp):
        app.register_blueprint(bp)

    # --- startup ---------------------------------------------------------------
    with app.app_context():
        init_db()
        from app.seed import run_seed

        run_seed()

    return app


def _static_exists(app: Flask, name: str) -> bool:
    return (BASE_DIR / "static" / name).exists()


app = create_app()
