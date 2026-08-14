"""Server-rendered page routes (Jinja2 templates)."""
from __future__ import annotations

from flask import Blueprint, abort, redirect, render_template, request, url_for

from app.config import settings
from app.dependencies import admin_required, current_user, login_required
from app.repositories.scan_repo import ScanRepository
from app.repositories.user_repo import UserRepository

bp = Blueprint("pages", __name__)


def _base_context(active: str = "") -> dict:
    user = current_user()
    return {
        "user": user,
        "active": active,
        "app_version": settings.app_version,
        "csrf_token": request.cookies.get("aegis_csrf", ""),
    }


@bp.get("/")
def home():
    return render_template("home.html", **_base_context("home"))


@bp.get("/login")
def login():
    if current_user():
        return redirect(url_for("pages.dashboard"))
    return render_template("login.html", **_base_context())


@bp.get("/register")
def register():
    if current_user():
        return redirect(url_for("pages.dashboard"))
    return render_template("register.html", **_base_context())


@bp.get("/forgot")
def forgot():
    return render_template("forgot.html", **_base_context())


@bp.get("/reset")
def reset():
    return render_template("reset.html", token=request.args.get("token", ""), **_base_context())


@bp.get("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", **_base_context("dashboard"))


@bp.get("/scan")
def scan():
    mode = request.args.get("mode", "url")
    return render_template("scan.html", mode=mode, **_base_context("scan"))


@bp.get("/report/<int:scan_id>")
def report(scan_id: int):
    from app.dependencies import db_session

    repo = ScanRepository(db_session())
    scan = repo.get(scan_id)
    if not scan:
        abort(404)
    user = current_user()
    # Allow access if scan is public OR user owns it
    if not scan.is_public and (not user or scan.user_id != user.id):
        abort(404)
    report_row = repo.get_report(scan_id)
    from app.trust_engine.engine import risk_level_for

    return render_template(
        "report.html",
        scan=scan,
        report=report_row,
        reasons=[f.to_dict() for f in scan.findings],
        risk_level_for=risk_level_for,
        **_base_context("report"),
    )


@bp.get("/map")
def map_page():
    return render_template("map.html", **_base_context("map"))


@bp.get("/learn")
@login_required
def learn():
    return render_template("learn.html", **_base_context("learn"))


@bp.get("/profile")
@login_required
def profile():
    user = current_user()
    return render_template("profile.html", **_base_context("profile"))


@bp.get("/admin")
@admin_required
def admin():
    return render_template("admin.html", **_base_context("admin"))


@bp.get("/search")
@login_required
def search_page():
    return render_template("search.html", query=request.args.get("q", ""),
                           **_base_context("search"))
