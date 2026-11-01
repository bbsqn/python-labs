"""Модуль валідації записів згідно бізнес-правил предметної області."""

from .exceptions import RecordValidationError
from .models import BankAccountRecord

ALLOWED_OPERATIONS = {"deposit", "withdraw"}


def parse_account(
    row: dict[str, str],
    *,
    line_number: int,
) -> BankAccountRecord:
    """Валідує поля банківського запису згідно правил Варіанта 4:

    - Номер рахунку та клієнт не порожні
    - Початковий баланс balance >= 0
    - Дозволені операції: deposit, withdraw
    - Сума операції amount > 0
    - Заборона від'ємного балансу після операції withdraw
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
            f"Баланс повинен бути числом: {bal_raw!r}",
            line_number=line_number,
            field="balance",
        ) from error

    if balance < 0:
        raise RecordValidationError(
            f"Баланс не може бути від'ємним: {balance}",
            line_number=line_number,
            field="balance",
        )

    operation = row.get("operation", "").strip().lower()
    if operation not in ALLOWED_OPERATIONS:
        msg = (
            f"Невідома операція {operation!r}. "
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
            f"Сума транзакції повинна бути числом: {amt_raw!r}",
            line_number=line_number,
            field="amount",
        ) from error

    if amount <= 0:
        raise RecordValidationError(
            f"Сума транзакції повинна бути більшою за нуль: {amount}",
            line_number=line_number,
            field="amount",
        )

    if operation == "deposit":
        new_balance = round(balance + amount, 2)
    elif operation == "withdraw":
        if balance < amount:
            msg = (
                f"Недостатньо коштів: баланс {balance:.2f} < "
                f"суми зняття {amount:.2f} (заборона від'ємного балансу)"
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
