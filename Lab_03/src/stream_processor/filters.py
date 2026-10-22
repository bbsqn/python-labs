"""Модуль потокової валідації та фільтрації записів."""

from collections.abc import Callable, Iterable, Iterator

from .models import AccountRecord

ALLOWED_OPERATIONS = {"deposit", "withdraw", "check"}


def validate_accounts(
    rows: Iterable[dict[str, str]],
) -> Iterator[AccountRecord]:
    """Потокова валідація рядків із пропуском некоректних даних."""
    for row in rows:
        try:
            acc_num = row.get("account_number", "").strip()
            client = row.get("client", "").strip()
            bal_str = row.get("balance", "")
            op = row.get("operation", "check").strip().lower()
            amt_str = row.get("amount", "0.0")

            if not acc_num or not client:
                continue

            balance = float(bal_str)
            amount = float(amt_str)

            if balance < 0 or amount < 0:
                continue

            if op not in ALLOWED_OPERATIONS:
                continue

            yield AccountRecord(
                account_number=acc_num,
                client=client,
                balance=balance,
                operation=op,
                amount=amount,
            )
        except (ValueError, TypeError, KeyError):
            continue


# Аліас для сумісності з універсальними тестами
validate_students = validate_accounts


def filter_by_balance(
    records: Iterable[AccountRecord],
    minimum_balance: float,
) -> Iterator[AccountRecord]:
    """Потокова фільтрація рахунків за мінімальним порогом балансу."""
    for record in records:
        if record.balance >= minimum_balance:
            yield record


# Аліас
filter_by_grade = filter_by_balance


def filter_by_client(
    records: Iterable[AccountRecord],
    client_name: str,
) -> Iterator[AccountRecord]:
    """Потокова фільтрація рахунків за клієнтом (підрядок, без регістру)."""
    target = client_name.strip().lower()
    for record in records:
        if target in record.client.lower():
            yield record


def find_first_account(
    records: Iterable[AccountRecord],
    predicate: Callable[[AccountRecord], bool],
) -> AccountRecord | None:
    """Lazy пошук першого запису з early termination (без матеріалізації)."""
    for record in records:
        if predicate(record):
            return record
    return None
