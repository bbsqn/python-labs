"""Валідація бізнес-правил банківських операцій."""

from .exceptions import (
    InvalidTransactionError,
    RecordValidationError,
)
from .models import BankAccountRecord

ALLOWED_OPERATIONS = {"deposit", "withdraw"}


def validate_account_number(account_number: str) -> str:
    """Перевірка коректності номера банківського рахунку."""
    cleaned = account_number.strip()
    if not cleaned:
        raise InvalidTransactionError("Номер рахунку не може бути порожнім.")
    if len(cleaned) < 5:
        raise InvalidTransactionError(
            f"Номер рахунку занадто короткий: {cleaned!r}"
        )
    return cleaned


def validate_amount(amount: float) -> float:
    """Перевірка коректності суми фінансової транзакції."""
    if amount <= 0:
        raise InvalidTransactionError(
            f"Сума операції має бути строго додатною: {amount}"
        )
    return round(float(amount), 2)


def parse_account(
    row: dict[str, str],
    *,
    line_number: int,
) -> BankAccountRecord:
    """Валідація та парсинг рядка банківської операції:

    - непорожні номер рахунку та клієнт
    - початковий баланс >= 0
    - дозволена операція: deposit, withdraw
    - сума операції > 0
    - запобігання від'ємному залишку для withdraw
    """
    account_number = row.get("account_number", "").strip()
    if not account_number:
        raise RecordValidationError(
            "Номер рахунку не може бути порожнім",
            line_number=line_number,
            field="account_number",
        )

    client = row.get("client", "").strip()
    if not client:
        raise RecordValidationError(
            "Ім'я клієнта не може бути порожнім",
            line_number=line_number,
            field="client",
        )

    bal_raw = row.get("balance", "")
    try:
        balance = float(bal_raw)
    except (TypeError, ValueError) as error:
        raise RecordValidationError(
            f"Некоректне числове значення балансу: {bal_raw!r}",
            line_number=line_number,
            field="balance",
        ) from error

    if balance < 0:
        raise RecordValidationError(
            f"Баланс рахунку не може бути від'ємним: {balance}",
            line_number=line_number,
            field="balance",
        )

    operation = row.get("operation", "").strip().lower()
    if operation not in ALLOWED_OPERATIONS:
        msg = (
            f"Невідома банківська операція {operation!r}. "
            f"Дозволені: {ALLOWED_OPERATIONS}"
        )
        raise RecordValidationError(
            msg,
            line_number=line_number,
            field="operation",
        )

    amt_raw = row.get("amount", "")
    try:
        amount = float(amt_raw)
    except (TypeError, ValueError) as error:
        raise RecordValidationError(
            f"Некоректне числове значення суми операції: {amt_raw!r}",
            line_number=line_number,
            field="amount",
        ) from error

    if amount <= 0:
        raise RecordValidationError(
            f"Сума операції має бути строго додатною: {amount}",
            line_number=line_number,
            field="amount",
        )

    if operation == "deposit":
        new_balance = round(balance + amount, 2)
    elif operation == "withdraw":
        if balance < amount:
            msg = (
                f"Недостатньо коштів: баланс {balance:.2f} < "
                f"сума зняття {amount:.2f} (заборона овердрафту)"
            )
            raise RecordValidationError(
                msg,
                line_number=line_number,
                field="amount",
            )
        new_balance = round(balance - amount, 2)
    else:
        new_balance = balance

    return BankAccountRecord(
        account_number=account_number,
        client=client,
        balance=balance,
        operation=operation,
        amount=amount,
        new_balance=new_balance,
    )
