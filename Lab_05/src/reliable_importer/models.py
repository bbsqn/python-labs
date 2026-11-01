"""Модуль моделей даних та структури конфігурації."""

from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class BankAccountRecord:
    """Незмінюваний валідований запис банківського рахунку та операції."""

    account_number: str
    client: str
    balance: float
    operation: str
    amount: float
    new_balance: float

    def to_dict(self) -> dict[str, object]:
        """Серіалізація сутності в словник для експорту в JSON."""
        return asdict(self)


# Аліаси
AccountRecord = BankAccountRecord
StudentRecord = BankAccountRecord


@dataclass(frozen=True, slots=True)
class ProcessingConfig:
    """Конфігурація параметрів обробки та фільтрації даних."""

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
