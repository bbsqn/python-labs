"""Конфігурація підключення до SQLite, створення рушія та фабрики сесій SQLAlchemy."""

from __future__ import annotations

import sqlite3
from typing import Any

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from .models import Base

DATABASE_URL = "sqlite:///bank_system.db"


@event.listens_for(Engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection: Any, _connection_record: Any) -> None:
    """Увімкнути перевірку зовнішніх ключів (FOREIGN KEY) для кожного з'єднання SQLite."""
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def create_sqlite_engine(database_url: str = DATABASE_URL, echo: bool = False) -> Engine:
    """Створити рушій SQLAlchemy для вказаного URL бази даних."""
    return create_engine(database_url, echo=echo)


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
