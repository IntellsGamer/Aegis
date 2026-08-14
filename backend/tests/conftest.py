"""Pytest fixtures: app + client using a throwaway SQLite database."""
import os
import tempfile

import pytest

_TEST_DB = tempfile.mktemp(prefix="aegis_test_", suffix=".db")
os.environ["AEGIS_ENVIRONMENT"] = "test"
os.environ["AEGIS_DATABASE_URL"] = f"sqlite:///{_TEST_DB}"
os.environ["AEGIS_EMAIL_ENABLED"] = "false"
os.environ["AEGIS_OCR_ENGINE"] = "tesseract"

from app import create_app  # noqa: E402


@pytest.fixture(scope="session")
def app():
    app = create_app()
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    yield app


@pytest.fixture()
def client(app):
    return app.test_client()
