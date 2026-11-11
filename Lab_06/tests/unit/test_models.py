"""Модульні тести доменних моделей та фінансових операцій (Account)."""

import pytest

from bank_system.exceptions import (
    AccountValidationError,
    InsufficientFundsError,
    InvalidAmountError,
)
from bank_system.models import Account


def test_account_creation_valid(sample_account: Account) -> None:
    """Перевірка успішної ініціалізації банківського рахунку з коректними даними."""
    assert sample_account.account_number == "UA10000001"
    assert sample_account.client == "Остап Зінчук"
    assert sample_account.balance == pytest.approx(1500.50)
    assert sample_account.currency == "UAH"
    assert sample_account.is_active is True


@pytest.mark.parametrize(
    "invalid_acc_num",
    ["", "   "],
    ids=["empty_string", "whitespace_only"],
)
def test_account_creation_empty_number_raises(invalid_acc_num: str) -> None:
    """Перевірка відхилення створення рахунку з порожнім номером."""
    with pytest.raises(AccountValidationError, match="Номер рахунку не може бути порожнім"):
        Account(account_number=invalid_acc_num, client="Тестовий Клієнт", balance=100.0)


@pytest.mark.parametrize(
    "invalid_client",
    ["", "   "],
    ids=["empty_name", "whitespace_name"],
)
def test_account_creation_empty_client_raises(invalid_client: str) -> None:
    """Перевірка відхилення створення рахунку з порожнім ім'ям клієнта."""
    with pytest.raises(AccountValidationError, match="Ім'я клієнта не може бути порожнім"):
        Account(account_number="UA12345678", client=invalid_client, balance=100.0)


def test_account_creation_negative_balance_raises() -> None:
    """Перевірка заборони ініціалізації рахунку з від'ємним початковим балансом."""
    with pytest.raises(AccountValidationError, match="Початковий баланс не може бути від'ємним"):
        Account(account_number="UA12345678", client="Іван Франко", balance=-50.0)


def test_deposit_increases_balance(sample_account: Account) -> None:
    """Перевірка коректного збільшення залишку при поповненні рахунку."""
    initial_balance = sample_account.balance
    new_balance = sample_account.deposit(250.75)

    assert new_balance == pytest.approx(initial_balance + 250.75)
    assert sample_account.balance == pytest.approx(1751.25)


@pytest.mark.parametrize(
    "invalid_amount",
    [0.0, -0.01, -100.0],
    ids=["zero_amount", "negative_cent", "large_negative"],
)
def test_deposit_invalid_amount_raises(sample_account: Account, invalid_amount: float) -> None:
    """Перевірка відхилення поповнення рахунку на недопустиму суму (<= 0)."""
    with pytest.raises(InvalidAmountError, match="Сума поповнення повинна бути додатною"):
        sample_account.deposit(invalid_amount)


def test_withdraw_decreases_balance(sample_account: Account) -> None:
    """Перевірка коректного зменшення залишку при знятті коштів."""
    initial_balance = sample_account.balance
    new_balance = sample_account.withdraw(500.50)

    assert new_balance == pytest.approx(initial_balance - 500.50)
    assert sample_account.balance == pytest.approx(1000.00)


def test_withdraw_boundary_exact_balance(sample_account: Account) -> None:
    """Граничне тестування: повне зняття всіх коштів під нуль."""
    balance_to_withdraw = sample_account.balance
    new_balance = sample_account.withdraw(balance_to_withdraw)

    assert new_balance == pytest.approx(0.0)
    assert sample_account.balance == pytest.approx(0.0)


def test_withdraw_insufficient_funds_raises(sample_account: Account) -> None:
    """Перевірка заборони зняття суми, що перевищує поточний баланс рахунку."""
    excessive_amount = sample_account.balance + 100.0
    with pytest.raises(InsufficientFundsError, match="Недостатньо коштів"):
        sample_account.withdraw(excessive_amount)


@pytest.mark.parametrize(
    "invalid_amount",
    [0.0, -10.0],
    ids=["zero_withdraw", "negative_withdraw"],
)
def test_withdraw_invalid_amount_raises(sample_account: Account, invalid_amount: float) -> None:
    """Перевірка відхилення операції зняття на недопустиму суму (<= 0)."""
    with pytest.raises(InvalidAmountError, match="Сума зняття повинна бути додатною"):
        sample_account.withdraw(invalid_amount)


def test_to_dict_serialization(sample_account: Account) -> None:
    """Перевірка коректності словникової серіалізації сутності рахунку."""
    data = sample_account.to_dict()
    assert data["account_number"] == "UA10000001"
    assert data["client"] == "Остап Зінчук"
    assert data["balance"] == pytest.approx(1500.50)
    assert data["currency"] == "UAH"
    assert data["is_active"] is True
