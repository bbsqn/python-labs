"""Інтеграційні тести CRUD-операцій, зв'язків, обмежень та SQLite FK."""

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from bank_system.exceptions import (
    AccountValidationError,
    DatabaseOperationError,
    InsufficientFundsError,
)
from bank_system.models import Account, Client, Transaction
from bank_system.repositories import (
    AccountRepository,
    ClientRepository,
    TransactionRepository,
)


def test_client_repository_crud_and_cascade(session: Session) -> None:
    """Перевірка Create, Read, Update, Delete клієнта та каскадного видалення рахунків."""
    client_repo = ClientRepository(session)
    account_repo = AccountRepository(session)

    created = client_repo.add("Петренко Іван", email="ivan@example.com")
    assert created.id is not None
    assert created.full_name == "Петренко Іван"

    loaded = client_repo.get_by_id(created.id)
    assert loaded is not None
    assert loaded.email == "ivan@example.com"

    updated = client_repo.update(created.id, full_name="Петренко Іван О.")
    assert updated is not None
    assert updated.full_name == "Петренко Іван О."

    acc = account_repo.add(
        Account(account_number="UA777", balance=200.0, client_id=created.id)
    )
    assert account_repo.get_by_id(acc.id) is not None

    deleted = client_repo.delete(created.id)
    assert deleted is True
    assert client_repo.get_by_id(created.id) is None
    assert account_repo.get_by_id(acc.id) is None


def test_account_repository_crud(
    session: Session,
    seeded_accounts: tuple[Client, Client, Account, Account],
) -> None:
    """Перевірка Create, Read, Update, Delete та пошуку для AccountRepository."""
    _, _, acc_a, _ = seeded_accounts
    account_repo = AccountRepository(session)

    by_num = account_repo.get_by_number("UA100001")
    assert by_num is not None
    assert by_num.client_name == "Зінчук Остап"
    assert by_num.check_balance() == pytest.approx(1000.0)

    all_accounts = account_repo.get_all()
    assert len(all_accounts) == 2

    updated = account_repo.update_balance(acc_a.id, 1750.50)
    assert updated is not None
    assert updated.balance == pytest.approx(1750.50)

    joined = account_repo.find_by_client_name("Анна")
    assert len(joined) == 1
    assert joined[0].account_number == "UA100002"

    assert account_repo.delete(acc_a.id) is True
    assert account_repo.get_by_id(acc_a.id) is None
    assert account_repo.delete(999999) is False


def test_unique_account_number_constraint(
    session: Session,
    seeded_accounts: tuple[Client, Client, Account, Account],
) -> None:
    """Перевірка UNIQUE constraint для номера рахунку та обробки IntegrityError."""
    client_a, _, _, _ = seeded_accounts
    account_repo = AccountRepository(session)

    with pytest.raises(DatabaseOperationError):
        account_repo.add(
            Account(
                account_number="UA100001",
                balance=100.0,
                client_id=client_a.id,
            )
        )


def test_sqlite_foreign_key_enforcement(session: Session) -> None:
    """Перевірка дотримання FOREIGN KEY у SQLite при неіснуючому client_id."""
    account_repo = AccountRepository(session)

    with pytest.raises(DatabaseOperationError):
        account_repo.add(
            Account(account_number="UA_ORPHAN", balance=50.0, client_id=999999)
        )


def test_negative_balance_forbidden_orm_and_db_check(
    session: Session,
    seeded_accounts: tuple[Client, Client, Account, Account],
) -> None:
    """Перевірка заборони від'ємного балансу як на рівні ORM, так і SQL CHECK constraint."""
    client_a, _, acc_a, _ = seeded_accounts

    with pytest.raises(InsufficientFundsError):
        Account(
            account_number="UA_NEG",
            balance=-10.0,
            client_id=client_a.id,
        )

    with pytest.raises(AccountValidationError):
        Account(
            account_number="   ",
            balance=0.0,
            client_id=client_a.id,
        )

    with pytest.raises(IntegrityError):
        session.execute(
            text("UPDATE accounts SET balance = -50.0 WHERE id = :acc_id"),
            {"acc_id": acc_a.id},
        )
        session.commit()
    session.rollback()


def test_transaction_repository_crud(
    session: Session,
    seeded_accounts: tuple[Client, Client, Account, Account],
) -> None:
    """Перевірка CRUD для TransactionRepository."""
    _, _, acc_a, _ = seeded_accounts
    tx_repo = TransactionRepository(session)

    tx = tx_repo.add(
        Transaction(
            account_id=acc_a.id,
            operation_type="deposit",
            amount=300.0,
            description="Тестовий запис",
        )
    )
    assert tx.id is not None
    assert tx_repo.get_by_id(tx.id) is not None
    assert len(tx_repo.get_by_account(acc_a.id)) == 1
    assert len(tx_repo.get_all()) == 1
    assert tx_repo.delete(tx.id) is True
    assert tx_repo.get_by_id(tx.id) is None
