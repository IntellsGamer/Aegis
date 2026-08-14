"""Database engine, session factory and declarative base.

Supports SQLite (development) and PostgreSQL (production) out of the box.
Sessions are created per-request by the Flask application and stored on `g`.
"""
from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


engine = create_engine(
    settings.database_url,
    echo=settings.database_echo,
    future=True,
    **settings.sqlalchemy_kwargs,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    class_=Session,
    future=True,
)


def init_db() -> None:
    """Create all tables (used in dev/tests; production uses Alembic)."""
    from app import models  # noqa: F401  (register all models)

    Base.metadata.create_all(bind=engine)
