"""Модульні тести конфігурації із застосуванням фікстури monkeypatch."""

import pytest

from bank_system.config import (
    BankingConfig,
    get_allowed_operations,
    get_default_currency,
    load_config,
)


def test_default_currency_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Перевірка читання валюти за замовчуванням зі змінної BANK_CURRENCY."""
    monkeypatch.setenv("BANK_CURRENCY", "EUR")
    assert get_default_currency() == "EUR"


def test_default_currency_fallback_when_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    """Перевірка дефолтного значення UAH при відсутності змінної в оточенні."""
    monkeypatch.delenv("BANK_CURRENCY", raising=False)
    assert get_default_currency() == "UAH"


def test_allowed_operations_parsing(monkeypatch: pytest.MonkeyPatch) -> None:
    """Перевірка парсингу дозволених операцій з конфігурації оточення."""
    monkeypatch.setenv("BANK_ALLOWED_OPERATIONS", "deposit, withdraw")
    ops = get_allowed_operations()
    assert ops == ("deposit", "withdraw")


def test_load_config_complete(monkeypatch: pytest.MonkeyPatch) -> None:
    """Перевірка повного завантаження об'єкта BankingConfig зі зміненими значеннями."""
    monkeypatch.setenv("BANK_CURRENCY", "USD")
    monkeypatch.setenv("BANK_ALLOWED_OPERATIONS", "deposit,transfer")
    monkeypatch.setenv("BANK_MAX_TRANSACTION_LIMIT", "250000.0")

    config = load_config()

    assert isinstance(config, BankingConfig)
    assert config.currency == "USD"
    assert config.allowed_operations == ("deposit", "transfer")
    assert config.max_transaction_limit == 250000.0


def test_load_config_invalid_limit_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    """Перевірка fallback-значення ліміту при некоректному рядку в конфігурації."""
    monkeypatch.setenv("BANK_MAX_TRANSACTION_LIMIT", "INVALID_LIMIT")
    config = load_config()
    assert config.max_transaction_limit == 100000.0


def test_banking_config_defaults() -> None:
    """Перевірка дефолтних параметрів датакласу BankingConfig."""
    cfg = BankingConfig(
        currency="UAH",
        allowed_operations=("deposit",),
        max_transaction_limit=50000.0,
    )
    assert cfg.currency == "UAH"
    assert cfg.allowed_operations == ("deposit",)
    assert cfg.max_transaction_limit == 50000.0


def test_allowed_operations_empty_string(monkeypatch: pytest.MonkeyPatch) -> None:
    """Перевірка поведінки при порожньому значенні BANK_ALLOWED_OPERATIONS."""
    monkeypatch.setenv("BANK_ALLOWED_OPERATIONS", "   ")
    ops = get_allowed_operations()
    assert ops == ()
