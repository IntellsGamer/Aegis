"""Cross-platform local and native-Windows entry point.

Run ``python run.py`` on Windows, Linux, or macOS for local development.  On
Windows production installations, set ``AEGIS_ENVIRONMENT=production`` and the
entry point uses Waitress instead of Gunicorn, which is POSIX-only.
"""
from __future__ import annotations

import os

from app import create_app
from app.config import settings

app = create_app()


def main() -> None:
    if os.name == "nt" and settings.is_production:
        try:
            from waitress import serve
        except ImportError as exc:  # pragma: no cover - dependency marker owns this
            raise RuntimeError(
                "Waitress is required for native Windows production serving. "
                "Run: py -m pip install -r requirements.txt"
            ) from exc
        serve(app, host=settings.host, port=settings.port, threads=8)
        return

    # Flask's development server is deliberately used for local work on every
    # supported desktop OS. Linux container deployments keep using Gunicorn via
    # the Dockerfile; native Windows production uses the Waitress branch above.
    debug = settings.debug or settings.environment == "development"
    app.run(host=settings.host, port=settings.port, debug=debug)


if __name__ == "__main__":
    main()
