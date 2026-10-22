"""Модуль потокової агрегації, статистики та роботи з itertools."""

from collections import Counter
from collections.abc import Iterable, Iterator
from itertools import accumulate, groupby, pairwise
from typing import Any

from .models import AccountRecord


def calculate_statistics(
    records: Iterable[AccountRecord],
) -> dict[str, Any]:
    """Обчислює зведену статистику за один потік без матеріалізації списку."""
    count = 0
    total = 0.0
    min_bal: float | None = None
    max_bal: float | None = None
    operations_counter: Counter[str] = Counter()
    clients_counter: Counter[str] = Counter()

    for rec in records:
        b = rec.balance
        count += 1
        total += b
        operations_counter[rec.operation] += 1
        clients_counter[rec.client] += 1

        if min_bal is None or b < min_bal:
            min_bal = b
        if max_bal is None or b > max_bal:
            max_bal = b

    avg = total / count if count else 0.0

    return {
        "count": count,
        "total": round(total, 2),
        "average": round(avg, 2),
        "minimum": min_bal,
        "maximum": max_bal,
        "operations": dict(operations_counter),
        "clients": dict(clients_counter),
        "groups": dict(operations_counter),  # для сумісності з тестами
    }


def streaming_total_funds(records: Iterable[AccountRecord]) -> float:
    """Обчислює загальну суму коштів у потоці через generator expression."""
    return round(sum(acc.balance for acc in records), 2)


def streaming_average_balance(records: Iterable[AccountRecord]) -> float:
    """Потокове середнє значення без збереження списку в пам'яті."""
    total = 0.0
    count = 0
    for acc in records:
        total += acc.balance
        count += 1
    return round(total / count, 2) if count else 0.0


def cumulative_balances(
    records: Iterable[AccountRecord],
) -> Iterator[float]:
    """Повертає кумулятивну динаміку сум за допомогою itertools.accumulate."""
    yield from accumulate(acc.balance for acc in records)


def pairwise_amount_differences(
    records: Iterable[AccountRecord],
) -> Iterator[float]:
    """Обчислює різниці послідовних сум операцій через itertools.pairwise."""
    amounts = (acc.amount for acc in records)
    for prev, curr in pairwise(amounts):
        yield round(curr - prev, 2)


def group_by_operation(
    records: list[AccountRecord],
) -> Iterator[tuple[str, list[AccountRecord]]]:
    """Групує записи за типом операції через itertools.groupby."""
    sorted_recs = sorted(records, key=lambda a: a.operation)
    for op, group in groupby(sorted_recs, key=lambda a: a.operation):
        yield op, list(group)
