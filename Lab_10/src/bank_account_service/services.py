"""Сервісний шар банківської системи: бізнес-логіка, агрегації та ACID-транзакції."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .exceptions import (
    AccountNotFoundError,
    InsufficientFundsError,
    InvalidAmountError,
)
from .models import Account, Client, Transaction
from .repositories import AccountRepository, TransactionRepository


def transfer_money(
    session: Session,
    from_account_number: str,
    to_account_number: str,
    amount: float,
) -> tuple[Account, Account]:
    """Атомарний переказ коштів між рахунками з фіксацією транзакцій або rollback при збої."""
    if amount <= 0:
        raise InvalidAmountError(f"Сума переказу повинна бути додатною, отримано: {amount:.2f}")
    if from_account_number == to_account_number:
        raise InvalidAmountError("Неможливо виконати переказ на той самий рахунок.")

    try:
        source_stmt = select(Account).where(Account.account_number == from_account_number)
        source = session.scalar(source_stmt)
        if source is None:
            raise AccountNotFoundError(f"Рахунок відправника {from_account_number} не знайдено.")

        if source.balance < amount:
            raise InsufficientFundsError(
                f"Недостатньо коштів на рахунку {from_account_number}: "
                f"доступно {source.balance:.2f}, запитано {amount:.2f}"
            )

        source.balance = round(source.balance - amount, 2)

        target_stmt = select(Account).where(Account.account_number == to_account_number)
        target = session.scalar(target_stmt)
        if target is None:
            raise AccountNotFoundError(f"Рахунок одержувача {to_account_number} не знайдено.")

        target.balance = round(target.balance + amount, 2)

        session.add(
            Transaction(
                account_id=source.id,
                operation_type="transfer_out",
                amount=amount,
                description=f"Переказ на рахунок {to_account_number}",
            )
        )
        session.add(
            Transaction(
                account_id=target.id,
                operation_type="transfer_in",
                amount=amount,
                description=f"Зарахування з рахунку {from_account_number}",
            )
        )

        session.commit()
        session.refresh(source)
        session.refresh(target)
        return source, target
    except Exception:
        session.rollback()
        raise


class BankService:
    """Сервіс бізнес-логіки банківських рахунків, відокремлений від шару SQL/ORM."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.account_repo = AccountRepository(session)
        self.tx_repo = TransactionRepository(session)

    def find_account(self, account_number: str) -> Account | None:
        """Знайти рахунок за номером."""
        return self.account_repo.get_by_number(account_number)

    def check_balance(self, account_number: str) -> float:
        """Перевірити поточний баланс рахунку."""
        account = self.account_repo.get_by_number(account_number)
        if account is None:
            raise AccountNotFoundError(f"Рахунок {account_number} не знайдено.")
        return account.balance

    def deposit(
        self,
        account_number: str,
        amount: float,
        description: str = "Поповнення рахунку",
    ) -> Account:
        """Поповнити рахунок і зберегти запис в історії транзакцій."""
        if amount <= 0:
            raise InvalidAmountError(
                f"Сума поповнення повинна бути додатною, отримано: {amount:.2f}"
            )
        try:
            account = self.account_repo.get_by_number(account_number)
            if account is None:
                raise AccountNotFoundError(f"Рахунок {account_number} не знайдено.")

            account.balance = round(account.balance + amount, 2)
            self.session.add(
                Transaction(
                    account_id=account.id,
                    operation_type="deposit",
                    amount=amount,
                    description=description,
                )
            )
            self.session.commit()
            self.session.refresh(account)
            return account
        except Exception:
            self.session.rollback()
            raise

    def withdraw(
        self,
        account_number: str,
        amount: float,
        description: str = "Зняття коштів",
    ) -> Account:
        """Зняти кошти з рахунку з контролем достатності балансу та історією операцій."""
        if amount <= 0:
            raise InvalidAmountError(f"Сума зняття повинна бути додатною, отримано: {amount:.2f}")
        try:
            account = self.account_repo.get_by_number(account_number)
            if account is None:
                raise AccountNotFoundError(f"Рахунок {account_number} не знайдено.")

            if account.balance < amount:
                raise InsufficientFundsError(
                    f"Недостатньо коштів на рахунку {account_number}: "
                    f"доступно {account.balance:.2f}, запитано {amount:.2f}"
                )

            account.balance = round(account.balance - amount, 2)
            self.session.add(
                Transaction(
                    account_id=account.id,
                    operation_type="withdraw",
                    amount=amount,
                    description=description,
                )
            )
            self.session.commit()
            self.session.refresh(account)
            return account
        except Exception:
            self.session.rollback()
            raise

    def transfer_money(
        self,
        from_account_number: str,
        to_account_number: str,
        amount: float,
    ) -> tuple[Account, Account]:
        """Виконати атомарний міжрахунковий переказ коштів."""
        return transfer_money(
            self.session,
            from_account_number,
            to_account_number,
            amount,
        )

    def get_total_funds(self) -> float:
        """Обчислити загальну суму коштів на всіх рахунках через SQL SUM()."""
        statement = select(func.sum(Account.balance))
        result = self.session.scalar(statement)
        if result is None:
            return 0.0
        return round(float(result), 2)

    def get_average_balance(self) -> float:
        """Обчислити середній баланс рахунків через SQL AVG()."""
        statement = select(func.avg(Account.balance))
        result = self.session.scalar(statement)
        if result is None:
            return 0.0
        return round(float(result), 2)

    def get_client_totals(self) -> list[tuple[str, float, int]]:
        """Отримати агреговану статистику по клієнтах (JOIN + GROUP BY + SUM + COUNT)."""
        statement = (
            select(
                Client.full_name,
                func.sum(Account.balance),
                func.count(Account.id),
            )
            .join(Account, Account.client_id == Client.id)
            .group_by(Client.id, Client.full_name)
            .order_by(Client.full_name)
        )
        rows = self.session.execute(statement).all()
        return [(str(row[0]), round(float(row[1]), 2), int(row[2])) for row in rows]

    def get_account_history(self, account_number: str) -> list[Transaction]:
        """Отримати історію транзакцій рахунку."""
        account = self.account_repo.get_by_number(account_number)
        if account is None:
            raise AccountNotFoundError(f"Рахунок {account_number} не знайдено.")
        return self.tx_repo.get_by_account(account.id)


BankingService = BankService
