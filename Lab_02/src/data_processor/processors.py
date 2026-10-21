"""Модуль обробки та перетворення даних рахунків (processors)."""

from collections import Counter, defaultdict
from collections.abc import Callable
from typing import Any


def get_unique_types(accounts: list[dict[str, Any]]) -> set[str]:
    """Повертає множину унікальних типів рахунків (set comprehension)."""
    return {
        str(acc.get("account_type", acc.get("group", "")))
        for acc in accounts
        if "account_type" in acc or "group" in acc
    }


get_unique_groups = get_unique_types


def create_account_index(
    accounts: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Створює індекс словника за номером рахунку (dict comprehension)."""
    return {
        str(acc.get("account_number", acc.get("id", ""))): acc
        for acc in accounts
    }


create_student_index = create_account_index


def find_account_by_number(
    accounts: list[dict[str, Any]],
    account_number: str,
) -> dict[str, Any] | None:
    """Лінійний пошук рахунку за номером у списку: складність O(n)."""
    for acc in accounts:
        if (
            acc.get("account_number") == account_number
            or str(acc.get("id")) == account_number
        ):
            return acc
    return None


find_linear = find_account_by_number


def find_account_by_index(
    index: dict[str, dict[str, Any]],
    account_number: str,
) -> dict[str, Any] | None:
    """Швидкий пошук рахунку за індексом у словнику: складність O(1)."""
    return index.get(account_number)


def filter_by_type(
    accounts: list[dict[str, Any]],
    account_type: str,
) -> list[dict[str, Any]]:
    """Фільтрує рахунки за типом (list comprehension)."""
    return [
        acc
        for acc in accounts
        if acc.get("account_type") == account_type
        or acc.get("group") == account_type
    ]


filter_by_group = filter_by_type


def filter_by_min_balance(
    accounts: list[dict[str, Any]],
    min_balance: float,
) -> list[dict[str, Any]]:
    """Фільтрує рахунки за мінімальним балансом (list comprehension)."""
    return [
        acc
        for acc in accounts
        if float(acc.get("balance", acc.get("grade", 0.0))) >= min_balance
    ]


def group_accounts_by_type(
    accounts: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    """Групує рахунки за типом за допомогою collections.defaultdict."""
    result: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for acc in accounts:
        acc_type = str(acc.get("account_type", acc.get("group", "other")))
        result[acc_type].append(acc)
    return dict(result)


group_students = group_accounts_by_type


def count_accounts_by_type(
    accounts: list[dict[str, Any]],
) -> Counter:
    """Підраховує кількість рахунків кожного типу через collections.Counter."""
    return Counter(
        str(acc.get("account_type", acc.get("group", "other")))
        for acc in accounts
    )


count_students_by_group = count_accounts_by_type


def filter_items(
    items: list[dict[str, Any]],
    predicate: Callable[[dict[str, Any]], bool],
) -> list[dict[str, Any]]:
    """Універсальна функція вищого порядку для фільтрації елементів."""
    return [item for item in items if predicate(item)]


def sort_accounts(
    accounts: list[dict[str, Any]],
    key_func: Callable[[dict[str, Any]], Any] | None = None,
    reverse: bool = False,
) -> list[dict[str, Any]]:
    """Універсальна функція сортування рахунків за переданим ключем."""
    if key_func is None:
        return sorted(
            accounts,
            key=lambda acc: float(acc.get("balance", acc.get("grade", 0.0))),
            reverse=reverse,
        )
    return sorted(accounts, key=key_func, reverse=reverse)


def group_by_nested(
    accounts: list[dict[str, Any]],
    primary_key: str = "account_type",
    secondary_key: str = "currency",
) -> dict[str, dict[str, list[dict[str, Any]]]]:
    """Вкладене групування рахунків за двома характеристиками (Advanced)."""
    grouped: defaultdict[str, defaultdict[str, list[dict[str, Any]]]] = (
        defaultdict(lambda: defaultdict(list))
    )
    for acc in accounts:
        p_val = str(acc.get(primary_key, "unknown"))
        s_val = str(acc.get(secondary_key, "unknown"))
        grouped[p_val][s_val].append(acc)
    return {k: dict(v) for k, v in grouped.items()}
