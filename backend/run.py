"""Native cross-platform AEGIS server entry point.

Direct launches use Waitress, a production WSGI server that works on Windows,
Linux, and macOS. Flask's built-in development server is available only when
``AEGIS_SERVER=flask`` is set explicitly for local framework debugging.
"""
from __future__ import annotations

import os

from app import create_app
from app.config import settings

app = create_app()


def resolve_server_mode() -> str:
    """Return the explicitly requested native server mode.

    Waitress is deliberately the default: ``python run.py`` must never quietly
    become Flask's development server merely because the environment is named
    ``development``.
    """
    mode = os.getenv("AEGIS_SERVER", "waitress").strip().lower()
    if mode not in {"waitress", "flask"}:
        raise RuntimeError("AEGIS_SERVER must be either 'waitress' or 'flask'.")
    return mode


def serve_with_waitress() -> None:
    """Start the application with the cross-platform production WSGI server."""
    try:
        from waitress import serve
    except ImportError as exc:  # pragma: no cover - protected by requirements
        raise RuntimeError(
            "Waitress is required for native AEGIS serving. "
            "Run the platform setup script or: py -m pip install -r requirements.txt"
        ) from exc

    print(f"AEGIS is serving with Waitress at http://{settings.host}:{settings.port}")
    serve(app, host=settings.host, port=settings.port, threads=8, ident="aegis")


def main() -> None:
    """Start the configured native server."""
    if resolve_server_mode() == "flask":
        print(f"AEGIS is serving with Flask development server at http://{settings.host}:{settings.port}")
        app.run(host=settings.host, port=settings.port, debug=True)
        return
    serve_with_waitress()


if __name__ == "__main__":
    main()
