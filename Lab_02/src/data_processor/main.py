"""Головний модуль демонстрації обробки даних банківської системи."""

import sys
import time
from pathlib import Path

# Додаємо директорію src до sys.path для підтримки прямого запуску
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data_processor.analytics import (  # noqa: E402
    OperationTracker,
    calculate_average_balance,
    calculate_average_values,
    calculate_total_funds,
    create_account_record,
    create_balance_filter,
    export_summary,
    find_poorest_account,
    find_richest_account,
    pipeline,
    sort_by_balance,
)
from data_processor.data import (  # noqa: E402
    ACCOUNTS_TUPLE,
    accounts,
)
from data_processor.decorators import repeat  # noqa: E402
from data_processor.processors import (  # noqa: E402
    count_accounts_by_type,
    create_account_index,
    filter_by_type,
    find_account_by_index,
    find_account_by_number,
    get_unique_types,
    group_accounts_by_type,
    group_by_nested,
)


def print_accounts(title: str, items: list[dict]) -> None:
    """Виводить список банківських рахунків у вигляді таблиці."""
    print(f"\n{title}")
    print("-" * 68)
    print(
        f"{'Номер':12} {'Клієнт':22} {'Тип':12} {'Баланс':>16}"
    )
    print("-" * 68)
    for acc in items:
        num = str(acc.get("account_number", acc.get("id", "")))
        name = str(acc.get("client_name", acc.get("name", "")))
        acc_type = str(acc.get("account_type", acc.get("group", "")))
        bal = float(acc.get("balance", acc.get("grade", 0.0)))
        print(f"{num:12} {name:22} {acc_type:12} {bal:>12.2f} UAH")


@repeat(count=2)
def ping_service() -> str:
    """Демонстрація параметризованого декоратора repeat."""
    return "Сервіс аналітики активний"


def run_benchmark() -> list[tuple[int, float, float]]:
    """Виконує порівняльний benchmark пошуку в list vs dict (Секція 37)."""
    sizes = [1_000, 10_000, 100_000]
    results: list[tuple[int, float, float]] = []

    for size in sizes:
        dataset = [
            {"account_number": f"UA{i:07d}", "balance": float(i)}
            for i in range(size)
        ]
        target_number = f"UA{size - 1:07d}"

        t0 = time.perf_counter()
        _ = find_account_by_number(dataset, target_number)
        t_list = time.perf_counter() - t0

        index = create_account_index(dataset)
        t0 = time.perf_counter()
        _ = find_account_by_index(index, target_number)
        t_dict = time.perf_counter() - t0

        results.append((size, t_list, t_dict))

    return results


def main() -> None:
    """Точка входу програми: повний цикл обробки структурованих даних."""
    print("=" * 68)
    print("ЛАБОРАТОРНА РОБОТА №2: СТРУКТУРИ ДАНИХ ТА ДЕКОМПОЗИЦІЯ")
    print("Варіант 4: Аналіз системи банківських рахунків")
    print("=" * 68)

    print_accounts("Усі банківські рахунки (list of dicts)", accounts)

    print(
        f"\nКількість елементів у кортежі (tuple): {len(ACCOUNTS_TUPLE)}"
    )

    unique_types = get_unique_types(accounts)
    print(f"\nУнікальні типи рахунків (set): {unique_types}")

    print("\n--- Агрегація та замір часу (@measure_time) ---")
    avg_balance = calculate_average_balance(accounts)
    total_funds = calculate_total_funds(accounts)
    print(f"Загальна сума коштів банку: {total_funds:.2f} UAH")
    print(f"Середній баланс: {avg_balance:.2f} UAH")

    richest = find_richest_account(accounts)
    poorest = find_poorest_account(accounts)
    if richest:
        print(
            f"\nНайбагатший рахунок (lambda max): {richest['account_number']} "
            f"({richest['client_name']}) — {richest['balance']:.2f} UAH"
        )
    if poorest:
        print(
            f"Найбідніший рахунок (lambda min): {poorest['account_number']} "
            f"({poorest['client_name']}) — {poorest['balance']:.2f} UAH"
        )

    ranking = sort_by_balance(accounts, reverse=True)
    print_accounts("Рейтинг рахунків за балансом (сортування lambda)", ranking)

    type_counter = count_accounts_by_type(accounts)
    print("\nКількість рахунків за типом (collections.Counter):")
    for t_name, count in type_counter.items():
        print(f"  • {t_name:12}: {count}")

    grouped = group_accounts_by_type(accounts)
    print("\nГрупування рахунків за типом (collections.defaultdict):")
    for t_name, accs in grouped.items():
        print(f"  • {t_name:12} -> {len(accs)} рахунків")

    nested_grouped = group_by_nested(accounts, "account_type", "currency")
    print(
        f"\nВкладене групування: {len(nested_grouped)} категорій"
    )

    index = create_account_index(accounts)
    search_num = "UA100005"
    found = find_account_by_index(index, search_num)
    print(f"\nПошук за номером {search_num} у dict-index (O(1)):")
    print(f"  {found}")

    threshold = 10_000.0
    min_filter = create_balance_filter(threshold)
    high_balance = [acc for acc in accounts if min_filter(acc)]
    print_accounts(
        f"Рахунки з балансом >= {threshold:.2f} UAH (closure filter)",
        high_balance,
    )

    sample_avg = calculate_average_values(15230.50, 4800.0, 980.75, 42100.0)
    print(f"\nСереднє значення через *args: {sample_avg:.2f}")

    new_account = create_account_record(
        account_number="UA100099",
        client_name="Остап Зінчук",
        balance=75000.00,
        account_type="deposit",
        currency="UAH",
    )
    print(f"\nНовий запис, створений через **kwargs:\n  {new_account}")

    status = ping_service()
    print(f"\nРезультат роботи @repeat(2): {status}")

    tracker = OperationTracker(maxlen=3)
    tracker.record_operation("Пошук UA100005")
    tracker.record_operation("Фільтрація балансу >= 10000")
    tracker.record_operation("Сортування рейтингу")
    tracker.record_operation("Експорт підсумку")
    print(f"\nОстанні 3 операції в deque: {tracker.get_recent()}")

    processed = pipeline(
        accounts,
        lambda d: filter_by_type(d, "savings"),
        lambda d: sort_by_balance(d, reverse=True),
    )
    print(
        f"\nРезультат pipeline (фільтр savings + сортування): "
        f"{len(processed)} записів"
    )

    summary = export_summary(accounts)
    print(
        f"\nПідсумковий звіт (export_summary):\n"
        f"  Всього: {summary['count']}, "
        f"Фонд: {summary['total_funds']:.2f} UAH, "
        f"Середній: {summary['average_balance']:.2f} UAH"
    )

    print("\n" + "=" * 68)
    print("ЕКСПЕРИМЕНТАЛЬНИЙ BENCHMARK (list search vs dict search)")
    print("=" * 68)
    print(
        f"{'Кількість records':<20} "
        f"{'list search (s)':<22} "
        f"{'dict search (s)':<22}"
    )
    print("-" * 68)
    bench_results = run_benchmark()
    for size, t_l, t_d in bench_results:
        print(f"{size:<20} {t_l:<22.8f} {t_d:<22.8f}")
    print("-" * 68)
    print(
        "Висновок: Пошук у dict (O(1)) працює в сотні разів швидше "
        "за list (O(n)) на великих даних."
    )


if __name__ == "__main__":
    main()
