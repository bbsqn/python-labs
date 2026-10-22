"""Головна точка входу для демонстрації потокового конвеєра (Lab 3)."""

# flake8: noqa: E402
from pathlib import Path
import sys

# Дозволяє запускати main.py безпосередньо як скрипт
SRC_DIR = str(Path(__file__).resolve().parent.parent)
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from itertools import islice

from stream_processor.analytics import (
    calculate_statistics,
    cumulative_balances,
    group_by_operation,
    pairwise_amount_differences,
    streaming_total_funds,
)
from stream_processor.batches import batched_records
from stream_processor.filters import find_first_account
from stream_processor.models import AccountRange
from stream_processor.parsers import (
    infinite_account_stream,
    recursive_flatten,
)
from stream_processor.pipeline import build_pipeline


def main() -> None:
    """Головна функція демонстрації можливостей конвеєра."""
    data_dir = Path(__file__).resolve().parent.parent.parent / "data"
    sample_path = data_dir / "sample.csv"
    accounts_path = data_dir / "accounts.csv"

    path = accounts_path if accounts_path.exists() else sample_path

    print("=" * 60)
    print("Лабораторна робота №3: Потокова обробка банківських рахунків")
    print(f"Вхідний файл: {path.name}")
    print("=" * 60)

    # 1. Демонстрація базового pipeline та itertools.islice
    min_balance = 500.0
    pipeline = build_pipeline(path, minimum_balance=min_balance)

    print(f"\n1. Перші 3 рахунки з балансом >= {min_balance} (через islice):")
    first_accounts = list(islice(pipeline, 3))
    for acc in first_accounts:
        print(
            f"   Рахунок: {acc.account_number} | "
            f"Клієнт: {acc.client:15} | "
            f"Баланс: {acc.balance:9.2f} | "
            f"Опер: {acc.operation:8} | "
            f"Сума: {acc.amount:7.2f}"
        )

    # 2. Демонстрація calculate_statistics
    # Pipeline є one-shot, тому створюємо його знову
    pipeline = build_pipeline(path, minimum_balance=0.0)
    stats = calculate_statistics(pipeline)
    print("\n2. Зведена потокова статистика рахунків:")
    print(f"   Кількість записів: {stats['count']}")
    print(f"   Загальні кошти:    {stats['total']:.2f}")
    print(f"   Середній баланс:   {stats['average']:.2f}")
    print(f"   Мінімум:           {stats['minimum']}")
    print(f"   Максимум:          {stats['maximum']}")
    print(f"   Операції:          {stats['operations']}")

    # 3. Generator expression для обчислення суми
    pipeline = build_pipeline(path, minimum_balance=0.0)
    gen_total = streaming_total_funds(pipeline)
    print(f"\n3. Загальна сума через generator expression: {gen_total:.2f}")

    # 4. Демонстрація фільтрації та early termination
    pipeline = build_pipeline(path, minimum_balance=0.0)
    found = find_first_account(
        pipeline,
        lambda a: a.balance > 2000.0
    )
    if found:
        print(
            f"\n4. Early termination (перший рахунок > 2000.0): "
            f"{found.account_number} ({found.client}: {found.balance:.2f})"
        )

    # 5. Демонстрація batching (пакетної обробки)
    pipeline = build_pipeline(path, minimum_balance=0.0)
    print("\n5. Пакетна обробка (batched_records, розмір пакета = 3):")
    batch_iter = batched_records(pipeline, batch_size=3)
    for i, batch in enumerate(islice(batch_iter, 2), 1):
        print(f"   Пакет #{i} (розмір: {len(batch)}):")
        for acc in batch:
            print(
                f"     -> {acc.account_number}: {acc.client} "
                f"({acc.balance:.2f})"
            )

    # 6. Демонстрація itertools.pairwise
    pipeline = build_pipeline(path, minimum_balance=0.0)
    sample_accs = list(islice(pipeline, 5))
    diffs = list(pairwise_amount_differences(sample_accs))
    print(f"\n6. Різниці послідовних сум операцій (pairwise): {diffs}")

    # 7. Демонстрація itertools.accumulate
    cum_bals = list(islice(cumulative_balances(sample_accs), 5))
    print(f"\n7. Кумулятивна сума балансів (accumulate): {cum_bals}")

    # 8. Демонстрація itertools.groupby
    grouped = list(group_by_operation(sample_accs))
    print("\n8. Групування записів за операцією (groupby):")
    for op, items in grouped:
        print(f"   Операція '{op}': {len(items)} записів")

    # 9. Демонстрація власного класу-ітератора AccountRange
    custom_range = AccountRange(101, 106)
    print(f"\n9. Власний iterable/iterator AccountRange: {list(custom_range)}")

    # 10. Демонстрація recursive flatten із yield from
    nested = [1, [2, 3], [4, [5, 6]]]
    flattened = list(recursive_flatten(nested))
    print(f"\n10. Рекурсивне сплощення yield from: {nested} -> {flattened}")

    # 11. Демонстрація нескінченного потоку та islice
    inf_stream = infinite_account_stream(1)
    inf_sample = list(islice(inf_stream, 3))
    print("\n11. Нескінченний потік (infinite stream + islice 3 елементи):")
    for acc in inf_sample:
        print(f"    -> {acc.account_number}: {acc.client} | {acc.balance:.2f}")

    print("\n" + "=" * 60)
    print("Демонстрація завершена успішно.")
    print("=" * 60)


if __name__ == "__main__":
    main()
