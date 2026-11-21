"""Шар доступу до даних (Repository Pattern) та DB-API параметризовані запити."""

from __future__ import annotations

import sqlite3

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .exceptions import DatabaseOperationError
from .models import Account, Client, Transaction


class ClientRepository:
    """Репозиторій для CRUD-операцій із клієнтами банку."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, full_name: str, email: str | None = None) -> Client:
        """Створити та зберегти нового клієнта у базі даних."""
        client = Client(full_name=full_name, email=email)
        try:
            self.session.add(client)
            self.session.commit()
            self.session.refresh(client)
            return client
        except IntegrityError as error:
            self.session.rollback()
            raise DatabaseOperationError(
                f"Помилка збереження клієнта '{full_name}': {error}"
            ) from error

    def get_by_id(self, client_id: int) -> Client | None:
        """Отримати клієнта за первинним ключем."""
        return self.session.get(Client, client_id)

    def get_by_name(self, full_name: str) -> Client | None:
        """Знайти клієнта за повним ім'ям."""
        statement = select(Client).where(Client.full_name == full_name)
        return self.session.scalar(statement)

    def get_all(self) -> list[Client]:
        """Отримати список усіх клієнтів."""
        statement = select(Client).order_by(Client.id)
        return list(self.session.scalars(statement))

    def update(
        self,
        client_id: int,
        full_name: str | None = None,
        email: str | None = None,
    ) -> Client | None:
        """Оновити дані клієнта."""
        client = self.get_by_id(client_id)
        if client is None:
            return None
        if full_name is not None:
            client.full_name = full_name
        if email is not None:
            client.email = email
        try:
            self.session.commit()
            self.session.refresh(client)
            return client
        except IntegrityError as error:
            self.session.rollback()
            raise DatabaseOperationError(
                f"Помилка оновлення клієнта id={client_id}: {error}"
            ) from error

    def delete(self, client_id: int) -> bool:
        """Видалити клієнта та каскадно пов'язані рахунки."""
        client = self.get_by_id(client_id)
        if client is None:
            return False
        self.session.delete(client)
        self.session.commit()
        return True


class AccountRepository:
    """Репозиторій для CRUD-операцій та пошуку банківських рахунків."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, account: Account) -> Account:
        """Додати новий банківський рахунок до бази даних."""
        try:
            self.session.add(account)
            self.session.commit()
            self.session.refresh(account)
            return account
        except IntegrityError as error:
            self.session.rollback()
            raise DatabaseOperationError(
                f"Порушення обмеження цілісності для рахунку '{account.account_number}': {error}"
            ) from error

    def get_by_id(self, account_id: int) -> Account | None:
        """Отримати рахунок за ідентифікатором."""
        return self.session.get(Account, account_id)

    def get_by_number(self, account_number: str) -> Account | None:
        """Знайти рахунок за унікальним номером рахунку."""
        statement = select(Account).where(Account.account_number == account_number)
        return self.session.scalar(statement)

    def get_all(self, limit: int | None = None, offset: int = 0) -> list[Account]:
        """Отримати список рахунків з опціональною пагінацією."""
        statement = select(Account).order_by(Account.id).offset(offset)
        if limit is not None:
            statement = statement.limit(limit)
        return list(self.session.scalars(statement))

    def search(
        self,
        client_id: int | None = None,
        account_type: str | None = None,
        min_balance: float | None = None,
        search_query: str | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[Account]:
        """Фільтрація та пагінація банківських рахунків за параметрами запиту."""
        statement = select(Account).order_by(Account.id)
        if client_id is not None:
            statement = statement.where(Account.client_id == client_id)
        if account_type is not None:
            statement = statement.where(Account.account_type == account_type)
        if min_balance is not None:
            statement = statement.where(Account.balance >= min_balance)
        if search_query is not None and search_query.strip():
            pattern = f"%{search_query.strip()}%"
            statement = statement.where(Account.account_number.ilike(pattern))
        statement = statement.offset(offset)
        if limit is not None:
            statement = statement.limit(limit)
        return list(self.session.scalars(statement))

    def find_by_client(self, client_id: int) -> list[Account]:
        """Отримати всі рахунки вказаного клієнта."""
        statement = select(Account).where(Account.client_id == client_id).order_by(Account.id)
        return list(self.session.scalars(statement))

    def find_by_client_name(self, name_query: str) -> list[Account]:
        """Знайти рахунки за ім'ям клієнта через SQL JOIN."""
        pattern = f"%{name_query.strip()}%"
        statement = (
            select(Account)
            .join(Client, Account.client_id == Client.id)
            .where(Client.full_name.ilike(pattern))
            .order_by(Account.id)
        )
        return list(self.session.scalars(statement))

    def update_balance(self, account_id: int, new_balance: float) -> Account | None:
        """Оновити баланс рахунку."""
        account = self.get_by_id(account_id)
        if account is None:
            return None
        account.balance = new_balance
        try:
            self.session.commit()
            self.session.refresh(account)
            return account
        except IntegrityError as error:
            self.session.rollback()
            raise DatabaseOperationError(
                f"Помилка оновлення балансу рахунку id={account_id}: {error}"
            ) from error

    def update_attributes(
        self,
        account_id: int,
        account_type: str | None = None,
        currency: str | None = None,
    ) -> Account | None:
        """Оновити метадані рахунку (тип рахунку або валюту)."""
        account = self.get_by_id(account_id)
        if account is None:
            return None
        if account_type is not None:
            account.account_type = account_type
        if currency is not None:
            account.currency = currency
        self.session.commit()
        self.session.refresh(account)
        return account

    def delete(self, account_id: int) -> bool:
        """Видалити банківський рахунок за ідентифікатором."""
        account = self.get_by_id(account_id)
        if account is None:
            return False
        self.session.delete(account)
        self.session.commit()
        return True


class TransactionRepository:
    """Репозиторій для роботи з історією банківських транзакцій."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, transaction: Transaction) -> Transaction:
        """Зберегти запис про транзакцію."""
        try:
            self.session.add(transaction)
            self.session.commit()
            self.session.refresh(transaction)
            return transaction
        except IntegrityError as error:
            self.session.rollback()
            raise DatabaseOperationError(f"Помилка збереження транзакції: {error}") from error

    def get_by_id(self, transaction_id: int) -> Transaction | None:
        """Отримати транзакцію за ідентифікатором."""
        return self.session.get(Transaction, transaction_id)

    def get_by_account(self, account_id: int) -> list[Transaction]:
        """Отримати історію транзакцій для вказаного рахунку."""
        statement = (
            select(Transaction).where(Transaction.account_id == account_id).order_by(Transaction.id)
        )
        return list(self.session.scalars(statement))

    def get_all(self) -> list[Transaction]:
        """Отримати всі транзакції."""
        statement = select(Transaction).order_by(Transaction.id)
        return list(self.session.scalars(statement))

    def delete(self, transaction_id: int) -> bool:
        """Видалити транзакцію за ідентифікатором."""
        tx = self.get_by_id(transaction_id)
        if tx is None:
            return False
        self.session.delete(tx)
        self.session.commit()
        return True


def find_account_by_number_dbapi(
    database_path: str,
    account_number: str,
) -> list[tuple[int, str, float, str, str]]:
    """Параметризований пошук рахунку за номером засобами чистого Python DB-API (sqlite3)."""
    connection = sqlite3.connect(database_path)
    try:
        connection.execute("PRAGMA foreign_keys=ON")
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT
                accounts.id,
                accounts.account_number,
                accounts.balance,
                accounts.currency,
                clients.full_name
            FROM accounts
            JOIN clients
                ON accounts.client_id = clients.id
            WHERE accounts.account_number = ?
            """,
            (account_number,),
        )
        rows = cursor.fetchall()
    finally:
        connection.close()
    return [(int(row[0]), str(row[1]), float(row[2]), str(row[3]), str(row[4])) for row in rows]
