"""Модульні тести валідаторів даних та банківських операцій."""

import pytest

from reliable_importer.exceptions import (
    InvalidTransactionError,
    RecordValidationError,
)
from reliable_importer.validators import (
    parse_account,
    validate_account_number,
    validate_amount,
)


def test_validate_account_number_valid() -> None:
    """Перевірка валідації коректних номерів банківських рахунків."""
    assert validate_account_number("UA12345678") == "UA12345678"
    assert validate_account_number("  UA87654321  ") == "UA87654321"


@pytest.mark.parametrize("invalid_acc", ["", "   ", "   \t\n  "])
def test_validate_account_number_empty(invalid_acc: str) -> None:
    """Порожній номер рахунку викликає InvalidTransactionError."""
    with pytest.raises(
        InvalidTransactionError,
        match="Номер рахунку не може бути порожнім",
    ):
        validate_account_number(invalid_acc)


def test_validate_account_number_too_short() -> None:
    """Занадто короткий номер рахунку викликає InvalidTransactionError."""
    with pytest.raises(
        InvalidTransactionError,
        match="Номер рахунку занадто короткий",
    ):
        validate_account_number("UA1")


def test_validate_amount_valid() -> None:
    """Перевірка валідації та заокруглення коректних сум транзакцій."""
    assert validate_amount(150.25) == pytest.approx(150.25)
    assert validate_amount(0.01) == pytest.approx(0.01)
    assert validate_amount(100.556) == pytest.approx(100.56)


@pytest.mark.parametrize("invalid_amt", [0.0, -0.01, -500.0])
def test_validate_amount_invalid(invalid_amt: float) -> None:
    """Нульові та від'ємні суми викликають InvalidTransactionError."""
    with pytest.raises(
        InvalidTransactionError,
        match="Сума операції має бути строго додатною",
    ):
        validate_amount(invalid_amt)


def test_parse_account_valid_deposit(
    sample_account_row: dict[str, str],
) -> None:
    """Перевірка успішного парсингу операції поповнення (deposit)."""
    record = parse_account(sample_account_row, line_number=2)
    assert record.account_number == "UA10000001"
    assert record.client == "Остап Зінчук"
    assert record.balance == pytest.approx(1500.50)
    assert record.operation == "deposit"
    assert record.amount == pytest.approx(200.00)
    assert record.new_balance == pytest.approx(1700.50)


def test_parse_account_valid_withdraw() -> None:
    """Перевірка успішного парсингу операції зняття (withdraw)."""
    row = {
        "account_number": "UA20000002",
        "client": "Марія Коваль",
        "balance": "1000.00",
        "operation": "withdraw",
        "amount": "250.00",
    }
    record = parse_account(row, line_number=5)
    assert record.account_number == "UA20000002"
    assert record.new_balance == pytest.approx(750.00)


@pytest.mark.parametrize(
    ("balance_str", "operation", "amount_str", "expected_new"),
    [
        ("0.00", "deposit", "100.00", 100.00),
        ("100.00", "withdraw", "100.00", 0.00),
        ("500.00", "deposit", "0.01", 500.01),
        ("500.00", "withdraw", "0.01", 499.99),
    ],
)
def test_parse_account_boundary_values(
    balance_str: str,
    operation: str,
    amount_str: str,
    expected_new: float,
) -> None:
    """Перевірка граничних сум та залишків при парсингу запису."""
    row = {
        "account_number": "UA_BOUNDARY",
        "client": "Тест Границі",
        "balance": balance_str,
        "operation": operation,
        "amount": amount_str,
    }
    record = parse_account(row, line_number=10)
    assert record.new_balance == pytest.approx(expected_new)


def test_parse_account_missing_account_number() -> None:
    """Перевірка винятку при відсутності номера рахунку."""
    row = {
        "account_number": "   ",
        "client": "Остап",
        "balance": "100.0",
        "operation": "deposit",
        "amount": "50.0",
    }
    with pytest.raises(RecordValidationError) as exc_info:
        parse_account(row, line_number=3)

    err = exc_info.value
    assert err.line_number == 3
    assert err.field == "account_number"
    assert "Номер рахунку" in str(err)


def test_parse_account_missing_client() -> None:
    """Перевірка винятку при відсутності імені клієнта."""
    row = {
        "account_number": "UA100",
        "client": "",
        "balance": "100.0",
        "operation": "deposit",
        "amount": "50.0",
    }
    with pytest.raises(RecordValidationError) as exc_info:
        parse_account(row, line_number=4)

    assert exc_info.value.field == "client"


def test_parse_account_invalid_balance_format() -> None:
    """Перевірка обробки нечислового значення балансу та ланцюжка винятків."""
    row = {
        "account_number": "UA100",
        "client": "Остап",
        "balance": "not_a_number",
        "operation": "deposit",
        "amount": "50.0",
    }
    with pytest.raises(RecordValidationError) as exc_info:
        parse_account(row, line_number=7)

    err = exc_info.value
    assert err.field == "balance"
    assert isinstance(err.__cause__, ValueError)


def test_parse_account_negative_balance() -> None:
    """Перевірка відхилення записів із від'ємним початковим балансом."""
    row = {
        "account_number": "UA100",
        "client": "Остап",
        "balance": "-50.00",
        "operation": "deposit",
        "amount": "50.0",
    }
    with pytest.raises(RecordValidationError) as exc_info:
        parse_account(row, line_number=8)

    assert exc_info.value.field == "balance"
    assert "не може бути від'ємним" in str(exc_info.value)


def test_parse_account_unknown_operation() -> None:
    """Перевірка відхилення непідтримуваних банківських операцій."""
    row = {
        "account_number": "UA100",
        "client": "Остап",
        "balance": "100.0",
        "operation": "unknown_op",
        "amount": "50.0",
    }
    with pytest.raises(RecordValidationError) as exc_info:
        parse_account(row, line_number=9)

    assert exc_info.value.field == "operation"
    assert "Невідома банківська операція" in str(exc_info.value)


def test_parse_account_invalid_amount_format() -> None:
    """Перевірка обробки нечислової суми транзакції з ланцюжком винятків."""
    row = {
        "account_number": "UA100",
        "client": "Остап",
        "balance": "100.0",
        "operation": "deposit",
        "amount": "bad_amount",
    }
    with pytest.raises(RecordValidationError) as exc_info:
        parse_account(row, line_number=11)

    err = exc_info.value
    assert err.field == "amount"
    assert isinstance(err.__cause__, ValueError)


@pytest.mark.parametrize("bad_amt", ["0.0", "-25.50"])
def test_parse_account_zero_or_negative_amount(bad_amt: str) -> None:
    """Перевірка заборони нульових та від'ємних сум транзакцій."""
    row = {
        "account_number": "UA100",
        "client": "Остап",
        "balance": "100.0",
        "operation": "deposit",
        "amount": bad_amt,
    }
    with pytest.raises(RecordValidationError) as exc_info:
        parse_account(row, line_number=12)

    assert exc_info.value.field == "amount"
    assert "строго додатною" in str(exc_info.value)


def test_parse_account_withdraw_overdraft_prevention() -> None:
    """Перевірка блокування овердрафту: сума зняття перевищує баланс."""
    row = {
        "account_number": "UA100",
        "client": "Остап",
        "balance": "300.00",
        "operation": "withdraw",
        "amount": "700.00",
    }
    with pytest.raises(RecordValidationError) as exc_info:
        parse_account(row, line_number=15)

    err = exc_info.value
    assert err.field == "amount"
    assert "Недостатньо коштів" in str(err)
