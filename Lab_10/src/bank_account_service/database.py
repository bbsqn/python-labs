"""Конфігурація підключення до БД через environment variables та SQLAlchemy."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

from .config import get_settings
from .models import Base

DATABASE_URL = get_settings().database_url


@event.listens_for(Engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection: Any, _connection_record: Any) -> None:
    """Увімкнути перевірку зовнішніх ключів (FOREIGN KEY) для кожного з'єднання SQLite."""
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def _ensure_sqlite_directory(database_url: str) -> None:
    """Створити батьківську директорію для файлової бази даних SQLite, якщо її не існує."""
    parsed = make_url(database_url)
    if parsed.get_backend_name() == "sqlite" and parsed.database and parsed.database != ":memory:":
        db_path = Path(parsed.database)
        db_path.parent.mkdir(parents=True, exist_ok=True)


def create_sqlite_engine(
    database_url: str | None = None,
    echo: bool = False,
) -> Engine:
    """Створити рушій SQLAlchemy для URL бази даних із конфігурації середовища."""
    target_url = database_url or get_settings().database_url
    _ensure_sqlite_directory(target_url)
    connect_args: dict[str, Any] = {}
    if target_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    return create_engine(target_url, echo=echo, connect_args=connect_args)


engine = create_sqlite_engine(DATABASE_URL, echo=False)

SessionLocal: sessionmaker[Session] = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)


def init_db(target_engine: Engine = engine) -> None:
    """Створити таблиці бази даних на основі ORM-метаданих."""
    Base.metadata.create_all(target_engine)


def get_dbapi_connection(database_path: str) -> sqlite3.Connection:
    """Відкрити пряме DB-API з'єднання з увімкненими зовнішніми ключами."""
    connection = sqlite3.connect(database_path)
    connection.execute("PRAGMA foreign_keys=ON")
    return connection
