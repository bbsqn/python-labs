"""Інтеграційні тести сервісу, ACID-транзакцій, rollback, DB-API та міграцій."""

from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect
from sqlalchemy.orm import Session, sessionmaker

from bank_system.database import create_sqlite_engine
from bank_system.exceptions import (
    AccountNotFoundError,
    InsufficientFundsError,
    InvalidAmountError,
)
from bank_system.models import Account, Base, Client
from bank_system.repositories import (
    AccountRepository,
    ClientRepository,
    find_account_by_number_dbapi,
)
from bank_system.services import BankService, transfer_money


def test_deposit_and_withdraw_operations(
    session: Session,
    seeded_accounts: tuple[Client, Client, Account, Account],
) -> None:
    """Перевірка поповнення, списання, перевірки балансу та історії операцій."""
    service = BankService(session)

    updated = service.deposit("UA100001", 250.0, "Аванс")
    assert updated.balance == pytest.approx(1250.0)

    updated_after = service.withdraw("UA100001", 200.0, "Покупка")
    assert updated_after.balance == pytest.approx(1050.0)
    assert service.check_balance("UA100001") == pytest.approx(1050.0)

    history = service.get_account_history("UA100001")
    assert len(history) == 2
    assert [tx.operation_type for tx in history] == ["deposit", "withdraw"]


def test_withdraw_insufficient_funds_and_invalid_amount(
    session: Session,
    seeded_accounts: tuple[Client, Client, Account, Account],
) -> None:
    """Перевірка заборони перевитрати балансу та некоректних сум."""
    service = BankService(session)

    with pytest.raises(InsufficientFundsError):
        service.withdraw("UA100002", 999.0)
    assert service.check_balance("UA100002") == pytest.approx(500.0)

    with pytest.raises(InvalidAmountError):
        service.deposit("UA100001", 0.0)

    with pytest.raises(InvalidAmountError):
        service.withdraw("UA100001", -50.0)


def test_sql_aggregations_total_average_and_group_by(
    session: Session,
    seeded_accounts: tuple[Client, Client, Account, Account],
) -> None:
    """Перевірка SQL SUM(), AVG(), COUNT() та GROUP BY по клієнтах."""
    client_a, _, _, _ = seeded_accounts
    AccountRepository(session).add(
        Account(
            account_number="UA100003",
            balance=500.0,
            client_id=client_a.id,
        )
    )
    service = BankService(session)

    assert service.get_total_funds() == pytest.approx(2000.0)
    assert service.get_average_balance() == pytest.approx(666.67)

    totals = service.get_client_totals()
    assert totals == [
        ("Зінчук Остап", 1500.0, 2),
        ("Коваль Анна", 500.0, 1),
    ]


def test_transfer_money_atomic_success(
    session: Session,
    seeded_accounts: tuple[Client, Client, Account, Account],
) -> None:
    """Перевірка успішного атомарного переказу між рахунками зі створенням транзакцій."""
    service = BankService(session)
    source, target = service.transfer_money("UA100001", "UA100002", 400.0)

    assert source.balance == pytest.approx(600.0)
    assert target.balance == pytest.approx(900.0)

    src_history = service.get_account_history("UA100001")
    tgt_history = service.get_account_history("UA100002")
    assert len(src_history) == 1
    assert src_history[0].operation_type == "transfer_out"
    assert len(tgt_history) == 1
    assert tgt_history[0].operation_type == "transfer_in"


def test_transfer_money_rollback_when_target_missing(
    session: Session,
    seeded_accounts: tuple[Client, Client, Account, Account],
) -> None:
    """Перевірка ACID Atomicity: списання відкочується, якщо одержувача немає."""
    service = BankService(session)

    with pytest.raises(AccountNotFoundError):
        transfer_money(session, "UA100001", "UA_UNKNOWN", 300.0)

    assert service.check_balance("UA100001") == pytest.approx(1000.0)
    assert service.get_account_history("UA100001") == []


def test_transfer_money_rollback_on_commit_failure(
    session: Session,
    seeded_accounts: tuple[Client, Client, Account, Account],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Перевірка повного rollback транзакції при збої фіксації змін у БД."""
    service = BankService(session)

    def broken_commit() -> None:
        raise RuntimeError("Simulated disk I/O error during commit")

    monkeypatch.setattr(session, "commit", broken_commit)

    with pytest.raises(RuntimeError, match="Simulated disk I/O error"):
        service.transfer_money("UA100001", "UA100002", 200.0)

    monkeypatch.undo()
    assert service.check_balance("UA100001") == pytest.approx(1000.0)
    assert service.check_balance("UA100002") == pytest.approx(500.0)


def test_dbapi_parameterized_query(file_db_path: Path) -> None:
    """Перевірка параметризованого DB-API пошуку (sqlite3) та захисту від SQL injection."""
    db_engine = create_sqlite_engine(f"sqlite:///{file_db_path}")
    Base.metadata.create_all(db_engine)
    factory = sessionmaker(bind=db_engine, expire_on_commit=False)

    with factory() as file_session:
        client = ClientRepository(file_session).add("Шевченко Тарас")
        AccountRepository(file_session).add(
            Account(account_number="UA900001", balance=3200.0, client_id=client.id)
        )
    db_engine.dispose()

    rows = find_account_by_number_dbapi(str(file_db_path), "UA900001")
    assert len(rows) == 1
    assert rows[0][1] == "UA900001"
    assert rows[0][2] == pytest.approx(3200.0)
    assert rows[0][4] == "Шевченко Тарас"

    injected = find_account_by_number_dbapi(str(file_db_path), "' OR '1'='1")
    assert injected == []


def test_alembic_migrations_upgrade_and_downgrade(file_db_path: Path) -> None:
    """Перевірка застосування (upgrade) та відкату (downgrade) міграцій Alembic."""
    lab_root = Path(__file__).resolve().parent.parent
    alembic_cfg = Config(str(lab_root / "alembic.ini"))
    alembic_cfg.set_main_option("script_location", str(lab_root / "migrations"))
    alembic_cfg.set_main_option("sqlalchemy.url", f"sqlite:///{file_db_path}")

    command.upgrade(alembic_cfg, "head")

    migrated_engine = create_sqlite_engine(f"sqlite:///{file_db_path}")
    inspector = inspect(migrated_engine)
    tables = set(inspector.get_table_names())
    assert {"clients", "accounts", "transactions"}.issubset(tables)

    account_columns = {col["name"] for col in inspector.get_columns("accounts")}
    assert {"account_type", "created_at"}.issubset(account_columns)
    migrated_engine.dispose()

    command.downgrade(alembic_cfg, "-1")
    downgraded_engine = create_sqlite_engine(f"sqlite:///{file_db_path}")
    downgraded_cols = {
        col["name"] for col in inspect(downgraded_engine).get_columns("accounts")
    }
    assert "account_type" not in downgraded_cols
    assert "created_at" not in downgraded_cols
    downgraded_engine.dispose()

    command.upgrade(alembic_cfg, "head")
