"""Демонстраційна точка входу: паралельність, оптимізація, кешування та синхронізація."""

from __future__ import annotations

import sys
from pathlib import Path
from time import perf_counter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bank_system.analytics import (  # noqa: E402
    BankAnalyticsLedger,
    calculate_balance_from_history_numpy,
    calculate_balance_from_history_python,
    generate_account_balances,
    generate_account_history,
    generate_operations,
    total_funds_numpy,
    total_funds_python,
    transaction_statistics_numpy,
    transaction_statistics_python,
)
from bank_system.parallel import (  # noqa: E402
    run_concurrent_account_simulation,
    transaction_statistics_processes,
    transaction_statistics_threads,
)


def run_optimization_demo() -> None:
    """Продемонструвати оптимізацію, паралельність, кешування та Lock для Варіанта 4."""
    balances = generate_account_balances(count=100_000, seed=42)
    _, _, amounts = generate_operations(count=500_000, account_count=100_000, seed=42)
    history = generate_account_history(count=500_000, seed=42)

    t0 = perf_counter()
    funds_py = total_funds_python(balances)
    t_funds_py = perf_counter() - t0

    t0 = perf_counter()
    funds_np = total_funds_numpy(balances)
    t_funds_np = perf_counter() - t0

    print(
        f"Загальна сума (100 000 рахунків): Python={funds_py:,.2f} ({t_funds_py:.6f}s) | "
        f"NumPy={funds_np:,.2f} ({t_funds_np:.6f}s)"
    )

    t0 = perf_counter()
    stats_py = transaction_statistics_python(amounts)
    t_stats_py = perf_counter() - t0

    t0 = perf_counter()
    stats_thr = transaction_statistics_threads(amounts, workers=4)
    t_stats_thr = perf_counter() - t0

    t0 = perf_counter()
    stats_proc = transaction_statistics_processes(amounts, workers=4)
    t_stats_proc = perf_counter() - t0

    t0 = perf_counter()
    stats_np = transaction_statistics_numpy(amounts)
    t_stats_np = perf_counter() - t0

    assert abs(stats_py["std"] - stats_np["std"]) < 1e-9
    assert abs(stats_py["std"] - stats_thr["std"]) < 1e-9
    assert abs(stats_py["std"] - stats_proc["std"]) < 1e-9

    print(
        f"Статистика 500 000 операцій: Python={t_stats_py:.6f}s | "
        f"Threads={t_stats_thr:.6f}s | Processes={t_stats_proc:.6f}s | "
        f"NumPy={t_stats_np:.6f}s"
    )

    hist_py = calculate_balance_from_history_python(10_000_000.0, history)
    hist_np = calculate_balance_from_history_numpy(10_000_000.0, history)
    assert abs(hist_py["final_balance"] - hist_np["final_balance"]) < 1e-6
    print(f"Баланс за історією 500 000 операцій: {hist_np}")

    ledger = BankAnalyticsLedger(maxsize=128)
    ledger.register_account(account_id=1, initial_balance=50_000.0, operations=amounts[:50_000])
    t0 = perf_counter()
    s1 = ledger.get_account_statistics(1)
    cold_t = perf_counter() - t0
    t0 = perf_counter()
    s2 = ledger.get_account_statistics(1)
    warm_t = perf_counter() - t0
    assert s1 == s2
    ledger.add_operation(account_id=1, operation_type="deposit", amount=1000.0)
    s3 = ledger.get_account_statistics(1)
    assert s3["count"] == 50_001.0
    print(
        f"Caching: cold={cold_t:.6f}s, warm={warm_t:.6f}s, "
        f"info={ledger.cache_info()}"
    )

    unsafe_res = run_concurrent_account_simulation(use_lock=False)
    safe_res = run_concurrent_account_simulation(use_lock=True)
    print("Без Lock (race condition):", unsafe_res)
    print("Із Lock (synchronization):", safe_res)


def main() -> None:
    """Точка входу програми."""
    run_optimization_demo()


if __name__ == "__main__":
    main()
