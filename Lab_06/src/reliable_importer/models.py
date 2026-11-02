"""Моделі даних предметної області: банківські рахунки."""

from dataclasses import asdict, dataclass
from pathlib import Path

from .exceptions import (
    InsufficientFundsError,
    InvalidTransactionError,
)


@dataclass(frozen=True, slots=True)
class BankAccountRecord:
    """Незмінний запис операції над банківським рахунком."""

    account_number: str
    client: str
    balance: float
    operation: str
    amount: float
    new_balance: float

    def to_dict(self) -> dict[str, object]:
        """Серіалізація об'єкта в словник для експорту в JSON."""
        return asdict(self)


AccountRecord = BankAccountRecord
StudentRecord = BankAccountRecord


class BankAccount:
    """Сутність банківського рахунку з підтримкою операцій."""

    def __init__(
        self,
        account_number: str,
        client: str,
        balance: float = 0.0,
        *,
        is_active: bool = True,
    ) -> None:
        if not account_number.strip():
            raise InvalidTransactionError(
                "Номер рахунку не може бути порожнім."
            )
        if not client.strip():
            raise InvalidTransactionError(
                "Ім'я клієнта не може бути порожнім."
            )
        if balance < 0:
            raise InvalidTransactionError(
                f"Початковий баланс не може бути від'ємним: {balance}"
            )
        self.account_number = account_number.strip()
        self.client = client.strip()
        self.balance = float(balance)
        self.is_active = is_active

    def deposit(self, amount: float) -> float:
        """Поповнення балансу рахунку."""
        if amount <= 0:
            raise InvalidTransactionError(
                f"Сума поповнення має бути додатньою: {amount}"
            )
        self.balance = round(self.balance + amount, 2)
        return self.balance

    def withdraw(self, amount: float) -> float:
        """Зняття коштів з рахунку із запобіганням овердрафту."""
        if amount <= 0:
            raise InvalidTransactionError(
                f"Сума зняття має бути додатньою: {amount}"
            )
        if amount > self.balance:
            raise InsufficientFundsError(
                self.account_number,
                self.balance,
                amount,
            )
        self.balance = round(self.balance - amount, 2)
        return self.balance

    def classify_tier(self) -> str:
        """Визначення категорії рахунку за поточним балансом.

        Використовується для тестування покриття розгалужень (Branch Coverage).
        """
        if self.balance < 0:
            raise InvalidTransactionError("Баланс не може бути від'ємним.")
        if self.balance < 1000.0:
            return "Standard"
        if self.balance < 5000.0:
            return "Silver"
        if self.balance < 20000.0:
            return "Gold"
        return "Platinum"

    def to_dict(self) -> dict[str, object]:
        """Конвертація рахунку в словник."""
        return {
            "account_number": self.account_number,
            "client": self.client,
            "balance": self.balance,
            "is_active": self.is_active,
            "tier": self.classify_tier(),
        }

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BankAccount):
            return NotImplemented
        return (
            self.account_number == other.account_number
            and self.client == other.client
            and abs(self.balance - other.balance) < 1e-6
            and self.is_active == other.is_active
        )

    def __repr__(self) -> str:
        return (
            f"BankAccount(account_number={self.account_number!r}, "
            f"client={self.client!r}, balance={self.balance}, "
            f"is_active={self.is_active})"
        )


@dataclass(frozen=True, slots=True)
class ProcessingConfig:
    """Конфігурація бізнес-обробки та фільтрації даних."""

    minimum_balance: float
    skip_invalid: bool


@dataclass(frozen=True, slots=True)
class LoggingConfig:
    """Конфігурація системи журналювання."""

    level: str
    path: Path


@dataclass(frozen=True, slots=True)
class AppConfig:
    """Головний об'єкт конфігурації додатку."""

    input_path: Path
    output_path: Path
    processing: ProcessingConfig
    logging: LoggingConfig
