"""WSGI entry point for Gunicorn and other process managers."""
from app import create_app
from app.config import settings

application = create_app()


if __name__ == "__main__":
    from waitress import serve

    print(f"AEGIS is serving with Waitress at http://{settings.host}:{settings.port}")
    serve(application, host=settings.host, port=settings.port, threads=8, ident="aegis")
