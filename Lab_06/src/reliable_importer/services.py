"""Сервіси бізнес-логіки, банківських операцій та імпорту."""

from collections.abc import Iterable, Iterator
from dataclasses import dataclass
import logging
from pathlib import Path
from typing import Protocol

from .exceptions import (
    AccountNotFoundError,
    RecordValidationError,
)
from .logging_config import mask_sensitive_account
from .models import BankAccount, BankAccountRecord
from .readers import read_csv_rows
from .validators import parse_account

logger = logging.getLogger(__name__)


@dataclass
class ImportStatistics:
    """Підсумкова статистика імпорту."""

    total: int = 0
    valid: int = 0
    invalid: int = 0
    exported: int = 0


def import_accounts(
    path: Path,
    *,
    skip_invalid: bool,
    statistics: ImportStatistics,
) -> Iterator[BankAccountRecord]:
    """Імпорт та валідація записів у режимах Strict / Tolerant:

    - Strict mode (skip_invalid=False): перша помилка перериває процес.
    - Tolerant mode (skip_invalid=True): некоректні записи пропускаються
      і логуються.
    """
    for line_number, row in read_csv_rows(path):
        statistics.total += 1
        try:
            account = parse_account(row, line_number=line_number)
        except RecordValidationError as error:
            statistics.invalid += 1
            acc_raw = row.get("account_number", "")
            masked = mask_sensitive_account(acc_raw)
            logger.warning(
                "Помилка валідації в рядку %s (рахунок %s, поле %s): %s",
                error.line_number,
                masked,
                error.field,
                error,
            )
            if skip_invalid:
                continue
            raise

        statistics.valid += 1
        yield account


def filter_by_balance(
    accounts: Iterable[BankAccountRecord],
    minimum_balance: float,
) -> Iterator[BankAccountRecord]:
    """Фільтрація рахунків за мінімальним порогом балансу."""
    for account in accounts:
        if account.balance >= minimum_balance:
            yield account


class AccountRepository(Protocol):
    """Протокол сховища банківських рахунків."""

    def add(self, account: BankAccount) -> None:
        """Додати рахунок до репозиторію."""
        ...

    def get(self, account_number: str) -> BankAccount | None:
        """Знайти рахунок за унікальним номером."""
        ...

    def list_all(self) -> list[BankAccount]:
        """Отримати список усіх зареєстрованих рахунків."""
        ...

    def total_funds(self) -> float:
        """Розрахувати сумарний обсяг коштів на всіх рахунках."""
        ...


class InMemoryAccountRepository:
    """In-Memory реалізація сховища рахунків для бізнес-логіки."""

    def __init__(self) -> None:
        self._accounts: dict[str, BankAccount] = {}

    def add(self, account: BankAccount) -> None:
        self._accounts[account.account_number] = account

    def get(self, account_number: str) -> BankAccount | None:
        return self._accounts.get(account_number)

    def list_all(self) -> list[BankAccount]:
        return list(self._accounts.values())

    def total_funds(self) -> float:
        total = sum(acc.balance for acc in self._accounts.values())
        return round(total, 2)


class Notifier(Protocol):
    """Протокол надсилання клієнтських сповіщень."""

    def notify(self, account_number: str, message: str) -> bool:
        """Надіслати повідомлення клієнту."""
        ...


class SMSNotifier:
    """Реалізація сповіщувача через SMS шлюз."""

    def notify(self, account_number: str, message: str) -> bool:
        logger.info("SMS для [%s]: %s", account_number, message)
        return True


class AsyncBankingGateway:
    """Асинхронний банківський шлюз для верифікації транзакцій."""

    def __init__(self, client: object) -> None:
        self._client = client

    async def verify_transaction(
        self,
        account_number: str,
        amount: float,
    ) -> str:
        """Асинхронна перевірка та авторизація транзакції."""
        client = self._client
        response = await client.authorize(  # type: ignore[attr-defined]
            account_number, amount
        )
        return str(response.get("status", "REJECTED"))


class BankingService:
    """Сервіс управління банківськими рахунками та транзакціями."""

    def __init__(
        self,
        repository: AccountRepository,
        notifier: Notifier,
        gateway: AsyncBankingGateway | None = None,
    ) -> None:
        self.repository = repository
        self.notifier = notifier
        self.gateway = gateway

    def create_account(
        self,
        account_number: str,
        client: str,
        initial_balance: float = 0.0,
    ) -> BankAccount:
        """Створення нового рахунку та реєстрація в системі."""
        account = BankAccount(
            account_number=account_number,
            client=client,
            balance=initial_balance,
        )
        self.repository.add(account)
        self.notifier.notify(
            account.account_number,
            f"Рахунок {account.account_number} успішно відкрито.",
        )
        return account

    def deposit(self, account_number: str, amount: float) -> float:
        """Поповнення рахунку із відправкою сповіщення."""
        account = self.repository.get(account_number)
        if account is None:
            raise AccountNotFoundError(account_number)

        new_bal = account.deposit(amount)
        self.notifier.notify(
            account_number,
            f"Поповнення {amount:.2f} грн. Баланс: {new_bal:.2f} грн.",
        )
        return new_bal

    def withdraw(self, account_number: str, amount: float) -> float:
        """Зняття коштів з рахунку із захистом від овердрафту."""
        account = self.repository.get(account_number)
        if account is None:
            raise AccountNotFoundError(account_number)

        new_bal = account.withdraw(amount)
        self.notifier.notify(
            account_number,
            f"Зняття {amount:.2f} грн. Новий баланс: {new_bal:.2f} грн.",
        )
        return new_bal

    def get_balance(self, account_number: str) -> float:
        """Отримання поточного залишку на рахунку."""
        account = self.repository.get(account_number)
        if account is None:
            raise AccountNotFoundError(account_number)
        return account.balance

    def get_total_funds(self) -> float:
        """Отримання сумарних коштів усього банку."""
        return self.repository.total_funds()

    async def execute_verified_transfer(
        self,
        account_number: str,
        amount: float,
    ) -> bool:
        """Асинхронне виконання верифікованої зовнішньої транзакції."""
        if self.gateway is None:
            return False

        status = await self.gateway.verify_transaction(account_number, amount)
        if status == "AUTHORIZED":
            self.withdraw(account_number, amount)
            return True
        return False
