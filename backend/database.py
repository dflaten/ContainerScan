from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from config import get_settings


class Base(DeclarativeBase):
    """Base SQLAlchemy declarative class for all ORM models."""

    pass


settings = get_settings()

engine = create_engine(settings.database_url, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db_session() -> Generator[Session, None, None]:
    """Yield a database session for the lifetime of one request.

    Yields:
        Session: An open SQLAlchemy session bound to the configured engine.
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
