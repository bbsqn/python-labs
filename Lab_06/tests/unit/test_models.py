"""Модульні тести доменних моделей та записів банківських операцій."""

from dataclasses import FrozenInstanceError

import pytest

from reliable_importer.exceptions import (
    InsufficientFundsError,
    InvalidTransactionError,
)
from reliable_importer.models import (
    BankAccount,
    BankAccountRecord,
)


def test_bank_account_record_creation(
    sample_record: BankAccountRecord,
) -> None:
    """Перевірка створення незмінного запису операції та to_dict()."""
    assert sample_record.account_number == "UA10000001"
    assert sample_record.client == "Остап Зінчук"
    assert sample_record.balance == pytest.approx(1500.50)
    assert sample_record.operation == "deposit"
    assert sample_record.amount == pytest.approx(200.00)
    assert sample_record.new_balance == pytest.approx(1700.50)

    data = sample_record.to_dict()
    assert isinstance(data, dict)
    assert data["account_number"] == "UA10000001"
    assert data["new_balance"] == pytest.approx(1700.50)


def test_bank_account_record_immutability(
    sample_record: BankAccountRecord,
) -> None:
    """Перевірка незмінності об'єкта BankAccountRecord (frozen=True)."""
    with pytest.raises((FrozenInstanceError, AttributeError)):
        sample_record.balance = 9999.0  # type: ignore[misc]


def test_bank_account_creation_valid() -> None:
    """Перевірка коректного створення доменного об'єкта рахунку."""
    acc = BankAccount(
        account_number="  UA12345678  ",
        client="  Остап Зінчук  ",
        balance=500.25,
    )
    assert acc.account_number == "UA12345678"
    assert acc.client == "Остап Зінчук"
    assert acc.balance == pytest.approx(500.25)
    assert acc.is_active is True


def test_bank_account_creation_empty_account_number() -> None:
    """Створення рахунку з порожнім номером має викликати виняток."""
    with pytest.raises(
        InvalidTransactionError,
        match="Номер рахунку не може бути порожнім",
    ):
        BankAccount(account_number="   ", client="Остап")


def test_bank_account_creation_empty_client() -> None:
    """Створення рахунку з порожнім клієнтом має викликати виняток."""
    with pytest.raises(
        InvalidTransactionError,
        match="Ім'я клієнта не може бути порожнім",
    ):
        BankAccount(account_number="UA123", client="   ")


def test_bank_account_creation_negative_balance() -> None:
    """Створення рахунку з від'ємним балансом має викликати виняток."""
    with pytest.raises(
        InvalidTransactionError,
        match="Початковий баланс не може бути від'ємним",
    ):
        BankAccount(account_number="UA123", client="Остап", balance=-10.0)


def test_bank_account_deposit_valid(sample_bank_account: BankAccount) -> None:
    """Перевірка поповнення рахунку та заокруглення (pytest.approx)."""
    new_bal = sample_bank_account.deposit(250.75)
    assert new_bal == pytest.approx(1751.25)
    assert sample_bank_account.balance == pytest.approx(1751.25)


@pytest.mark.parametrize("invalid_amount", [0.0, -0.01, -100.0])
def test_bank_account_deposit_invalid_amount(
    sample_bank_account: BankAccount,
    invalid_amount: float,
) -> None:
    """Поповнення нульовою чи від'ємною сумою має викликати помилку."""
    with pytest.raises(
        InvalidTransactionError,
        match="Сума поповнення має бути додатньою",
    ):
        sample_bank_account.deposit(invalid_amount)


def test_bank_account_withdraw_valid(sample_bank_account: BankAccount) -> None:
    """Перевірка успішного зняття коштів у межах доступного залишку."""
    new_bal = sample_bank_account.withdraw(500.50)
    assert new_bal == pytest.approx(1000.00)
    assert sample_bank_account.balance == pytest.approx(1000.00)


def test_bank_account_withdraw_exact_balance(
    sample_bank_account: BankAccount,
) -> None:
    """Перевірка зняття суми, що точно дорівнює залишковому балансу."""
    new_bal = sample_bank_account.withdraw(1500.50)
    assert new_bal == pytest.approx(0.0)
    assert sample_bank_account.balance == pytest.approx(0.0)


def test_bank_account_withdraw_insufficient_funds(
    sample_bank_account: BankAccount,
) -> None:
    """Спроба овердрафту має викликати InsufficientFundsError."""
    with pytest.raises(InsufficientFundsError) as exc_info:
        sample_bank_account.withdraw(2000.00)

    err = exc_info.value
    assert err.account_number == "UA10000001"
    assert err.balance == pytest.approx(1500.50)
    assert err.amount == pytest.approx(2000.00)
    assert "Недостатньо коштів" in str(err)


@pytest.mark.parametrize("invalid_amount", [0.0, -10.0])
def test_bank_account_withdraw_invalid_amount(
    sample_bank_account: BankAccount,
    invalid_amount: float,
) -> None:
    """Зняття некоректної суми має викликати помилку."""
    with pytest.raises(
        InvalidTransactionError,
        match="Сума зняття має бути додатньою",
    ):
        sample_bank_account.withdraw(invalid_amount)


@pytest.mark.parametrize(
    ("balance", "expected_tier"),
    [
        (0.0, "Standard"),
        (500.0, "Standard"),
        (999.99, "Standard"),
        (1000.0, "Silver"),
        (4999.99, "Silver"),
        (5000.0, "Gold"),
        (19999.99, "Gold"),
        (20000.0, "Platinum"),
        (50000.0, "Platinum"),
    ],
)
def test_bank_account_classify_tier(
    balance: float,
    expected_tier: str,
) -> None:
    """Перевірка категоризації рахунків для повного покриття розгалужень."""
    acc = BankAccount(
        account_number="UA_TIER_TEST",
        client="Тестер",
        balance=balance,
    )
    assert acc.classify_tier() == expected_tier


def test_bank_account_classify_tier_negative_raises() -> None:
    """Від'ємний баланс у classify_tier має викликати помилку."""
    acc = BankAccount("UA_TIER_TEST", "Тестер", 100.0)
    acc.balance = -5.0
    with pytest.raises(
        InvalidTransactionError,
        match="Баланс не може бути від'ємним",
    ):
        acc.classify_tier()


def test_bank_account_to_dict_and_representation(
    sample_bank_account: BankAccount,
) -> None:
    """Перевірка серіалізації в словник, __eq__ та __repr__."""
    data = sample_bank_account.to_dict()
    assert data["account_number"] == "UA10000001"
    assert data["tier"] == "Silver"
    assert data["is_active"] is True

    acc_same = BankAccount("UA10000001", "Остап Зінчук", 1500.50)
    assert sample_bank_account == acc_same
    assert sample_bank_account != "non_account_object"

    rep = repr(sample_bank_account)
    assert "UA10000001" in rep
    assert "Остап Зінчук" in rep
