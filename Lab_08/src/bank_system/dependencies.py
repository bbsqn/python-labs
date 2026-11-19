"""Залежності FastAPI для надання сесій SQLAlchemy."""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy.orm import Session

from .database import SessionLocal


def get_session() -> Generator[Session, None, None]:
    """Dependency, що відкриває сесію БД на час обробки HTTP-запиту."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
