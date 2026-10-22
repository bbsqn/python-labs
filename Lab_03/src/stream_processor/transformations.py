"""Модуль потокових трансформацій та застосування банківських операцій."""

from collections.abc import Iterable, Iterator

from .models import AccountRecord


def apply_operations(
    records: Iterable[AccountRecord],
) -> Iterator[AccountRecord]:
    """Потокове застосування операцій із захистом від від'ємного балансу."""
    for rec in records:
        current_balance = rec.balance
        op = rec.operation
        amt = rec.amount

        if op == "deposit":
            new_balance = round(current_balance + amt, 2)
        elif op == "withdraw":
            # Недопущення від'ємного балансу
            if current_balance >= amt:
                new_balance = round(current_balance - amt, 2)
            else:
                # Операція відхилена через нестачу коштів
                new_balance = current_balance
        else:
            new_balance = current_balance

        yield rec._replace(balance=new_balance)


def normalize_clients(
    records: Iterable[AccountRecord],
) -> Iterator[AccountRecord]:
    """Нормалізує імена клієнтів (title case, очищення пробілів)."""
    for rec in records:
        yield rec._replace(client=rec.client.strip().title())


# Аліас
normalize_names = normalize_clients
