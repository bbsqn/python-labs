"""Конфігурація фікстур тестової бази даних та FastAPI клієнта."""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from bank_system.api import app
from bank_system.dependencies import get_session
from bank_system.models import Account, Base, Client
from bank_system.repositories import AccountRepository, ClientRepository


@pytest.fixture
def engine_memory() -> Generator[Engine, None, None]:
    """Створити потокобезпечний ізольований in-memory рушій SQLite зі StaticPool."""
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(test_engine, "connect")
    def _enable_fk(dbapi_connection: object, _record: object) -> None:
        cursor = dbapi_connection.cursor()  # type: ignore[attr-defined]
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(test_engine)
    yield test_engine
    Base.metadata.drop_all(test_engine)
    test_engine.dispose()


@pytest.fixture
def session(engine_memory: Engine) -> Generator[Session, None, None]:
    """Створити ізольовану сесію БД і перевизначити залежність get_session для FastAPI."""
    test_session_factory = sessionmaker(
        bind=engine_memory,
        autoflush=False,
        expire_on_commit=False,
    )

    def _override_get_session() -> Generator[Session, None, None]:
        with test_session_factory() as db_session:
            yield db_session

    app.dependency_overrides[get_session] = _override_get_session
    with test_session_factory() as db_session:
        yield db_session
    app.dependency_overrides.clear()


@pytest.fixture
def client(session: Session) -> Generator[TestClient, None, None]:
    """Повернути синхронний TestClient FastAPI з ізольованою тестовою БД."""
    with TestClient(app) as test_client:
        yield test_client


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
