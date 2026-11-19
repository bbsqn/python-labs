"""Конфігурація фікстур тестової бази даних SQLite для integration tests."""

from collections.abc import Generator
from pathlib import Path

import pytest
from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from bank_system.database import create_sqlite_engine
from bank_system.models import Account, Base, Client
from bank_system.repositories import AccountRepository, ClientRepository


@pytest.fixture
def engine_memory() -> Generator[Engine, None, None]:
    """Створити ізольований in-memory рушій SQLite із зовнішніми ключами."""
    test_engine = create_sqlite_engine("sqlite:///:memory:")
    Base.metadata.create_all(test_engine)
    yield test_engine
    Base.metadata.drop_all(test_engine)
    test_engine.dispose()


@pytest.fixture
def session(engine_memory: Engine) -> Generator[Session, None, None]:
    """Створити ізольовану сесію SQLAlchemy для кожного тесту."""
    test_session_factory = sessionmaker(
        bind=engine_memory,
        autoflush=False,
        expire_on_commit=False,
    )
    with test_session_factory() as db_session:
        yield db_session


@pytest.fixture
def seeded_accounts(session: Session) -> tuple[Client, Client, Account, Account]:
    """Заповнити тестову БД двома клієнтами та двома рахунками."""
    client_repo = ClientRepository(session)
    account_repo = AccountRepository(session)

    client_a = client_repo.add("Зінчук Остап", email="ostap@example.com")
    client_b = client_repo.add("Коваль Анна", email="anna@example.com")

    acc_a = account_repo.add(
        Account(
            account_number="UA100001",
            balance=1000.0,
            currency="UAH",
            account_type="checking",
            client_id=client_a.id,
        )
    )
    acc_b = account_repo.add(
        Account(
            account_number="UA100002",
            balance=500.0,
            currency="UAH",
            account_type="savings",
            client_id=client_b.id,
        )
    )
    return client_a, client_b, acc_a, acc_b


@pytest.fixture
def file_db_path(tmp_path: Path) -> Path:
    """Повернути шлях до тимчасової файлової SQLite БД."""
    return tmp_path / "test_bank.db"
