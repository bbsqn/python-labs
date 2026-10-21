"""Модуль аналітики, агрегації, замикань та операцій над рахунками."""

from collections import deque
from collections.abc import Callable
from typing import Any

from .decorators import measure_time


def calculate_total_funds(accounts: list[dict[str, Any]]) -> float:
    """Агрегує загальну суму коштів на всіх рахунках."""
    return sum(
        float(acc.get("balance", acc.get("grade", 0.0)))
        for acc in accounts
    )


@measure_time
def calculate_average_balance(accounts: list[dict[str, Any]]) -> float:
    """Обчислює середній баланс рахунків (генераторний вираз)."""
    if not accounts:
        return 0.0
    return sum(
        float(acc.get("balance", acc.get("grade", 0.0)))
        for acc in accounts
    ) / len(accounts)


calculate_average = calculate_average_balance


def find_richest_account(
    accounts: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Знаходить рахунок з найбільшим балансом за допомогою lambda."""
    if not accounts:
        return None
    return max(
        accounts,
        key=lambda acc: float(acc.get("balance", acc.get("grade", 0.0))),
    )


find_best_student = find_richest_account


def find_poorest_account(
    accounts: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Знаходить рахунок з найменшим балансом за допомогою lambda."""
    if not accounts:
        return None
    return min(
        accounts,
        key=lambda acc: float(acc.get("balance", acc.get("grade", 0.0))),
    )


def sort_by_balance(
    accounts: list[dict[str, Any]],
    reverse: bool = True,
) -> list[dict[str, Any]]:
    """Сортує рахунки за балансом за спаданням/зростанням через lambda."""
    return sorted(
        accounts,
        key=lambda acc: float(acc.get("balance", acc.get("grade", 0.0))),
        reverse=reverse,
    )


sort_by_grade = sort_by_balance


def calculate_average_values(*values: float) -> float:
    """Обчислює середнє значення позиційних аргументів (*args)."""
    if not values:
        return 0.0
    return sum(values) / len(values)


def create_account_record(**fields: Any) -> dict[str, Any]:
    """Створює запис рахунку з довільних іменованих аргументів (**kwargs)."""
    return dict(fields)


create_record = create_account_record


def create_balance_filter(
    minimum_balance: float,
) -> Callable[[dict[str, Any]], bool]:
    """Створює фільтр замикання (closure), що пам'ятає пороговий баланс."""

    def predicate(account: dict[str, Any]) -> bool:
        return float(
            account.get("balance", account.get("grade", 0.0))
        ) >= minimum_balance

    return predicate


create_grade_filter = create_balance_filter


def create_type_filter(
    target_type: str,
) -> Callable[[dict[str, Any]], bool]:
    """Створює замикання (closure) для фільтрації за типом рахунку."""

    def predicate(account: dict[str, Any]) -> bool:
        return (
            account.get("account_type") == target_type
            or account.get("group") == target_type
        )

    return predicate


class OperationTracker:
    """Клас збереження історії операцій через collections.deque."""

    def __init__(self, maxlen: int = 10) -> None:
        self.history: deque[str] = deque(maxlen=maxlen)

    def record_operation(self, operation: str) -> None:
        """Додає операцію в історію з автоматичним витісненням."""
        self.history.append(operation)

    def get_recent(self) -> list[str]:
        """Повертає список останніх операцій."""
        return list(self.history)


def export_summary(accounts: list[dict[str, Any]]) -> dict[str, Any]:
    """Формує підсумковий звіт по рахунках у вигляді словника."""
    total = calculate_total_funds(accounts)
    avg = calculate_average_balance(accounts)
    richest = find_richest_account(accounts)
    poorest = find_poorest_account(accounts)
    return {
        "count": len(accounts),
        "total_funds": total,
        "average_balance": avg,
        "richest_account": richest,
        "poorest_account": poorest,
    }


def pipeline(
    data: list[dict[str, Any]],
    *operations: Callable[[list[dict[str, Any]]], list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    """Виконує ланцюжок трансформацій (Pipeline Processing)."""
    result = data
    for op in operations:
        result = op(result)
    return result
