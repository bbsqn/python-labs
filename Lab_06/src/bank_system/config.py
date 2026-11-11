"""Конфігурація банківської системи та робота зі змінними оточення."""

from dataclasses import dataclass
import os


@dataclass(frozen=True, slots=True)
class BankingConfig:
    """Незмінний об'єкт конфігурації параметрів банківської системи."""

    currency: str
    allowed_operations: tuple[str, ...]
    max_transaction_limit: float


def get_default_currency() -> str:
    """Отримати валюту за замовчуванням зі змінних середовища."""
    return os.getenv("BANK_CURRENCY", "UAH")


def get_allowed_operations() -> tuple[str, ...]:
    """Отримати список дозволених банківських операцій."""
    raw_ops = os.getenv("BANK_ALLOWED_OPERATIONS", "deposit,withdraw,transfer")
    return tuple(op.strip() for op in raw_ops.split(",") if op.strip())


def load_config() -> BankingConfig:
    """Завантажити повну конфігурацію системи з оточення."""
    limit_str = os.getenv("BANK_MAX_TRANSACTION_LIMIT", "100000.0")
    try:
        limit = float(limit_str)
    except ValueError:
        limit = 100000.0

    return BankingConfig(
        currency=get_default_currency(),
        allowed_operations=get_allowed_operations(),
        max_transaction_limit=limit,
    )

