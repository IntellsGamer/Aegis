"""Native server selection must default to a production WSGI server."""
import pytest

import run


def test_native_run_defaults_to_waitress(monkeypatch):
    monkeypatch.delenv("AEGIS_SERVER", raising=False)
    assert run.resolve_server_mode() == "waitress"


def test_flask_server_is_an_explicit_opt_in(monkeypatch):
    monkeypatch.setenv("AEGIS_SERVER", "flask")
    assert run.resolve_server_mode() == "flask"


def test_invalid_native_server_mode_is_rejected(monkeypatch):
    monkeypatch.setenv("AEGIS_SERVER", "gunicorn")
    with pytest.raises(RuntimeError, match="AEGIS_SERVER"):
        run.resolve_server_mode()
