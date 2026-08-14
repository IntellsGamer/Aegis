"""WSGI entry point for gunicorn: `gunicorn wsgi:application`."""
from app import create_app

application = create_app()

if __name__ == "__main__":
    application.run(host="0.0.0.0", port=8000, debug=application.config["DEBUG"])
