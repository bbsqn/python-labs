"""Профілювання продуктивності та пам'яті: timeit, cProfile і tracemalloc."""

from __future__ import annotations

import cProfile
import io
import pstats
import sys
import tracemalloc
from pathlib import Path
from timeit import timeit
from typing import Any

import numpy as np

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bank_account_service.analytics import (
    calculate_balance_from_history_numpy,
    calculate_balance_from_history_python,
    calculate_risk_scores_numpy,
    calculate_risk_scores_sequential,
    generate_account_balances,
    generate_account_history,
    generate_operations,
    total_funds_numpy,
    total_funds_python,
    transaction_statistics_numpy,
    transaction_statistics_python,
)


def run_timeit_comparison(
    account_count: int = 100_000,
    operation_count: int = 500_000,
    repeats: int = 5,
) -> dict[str, float]:
    """Виміряти час окремих операцій банківської аналітики через timeit."""
    balances = generate_account_balances(count=account_count, seed=42)
    _, _, amounts = generate_operations(
        count=operation_count,
        account_count=account_count,
        seed=42,
    )
    balances_np = np.asarray(balances, dtype=np.float64)
    amounts_np = np.asarray(amounts, dtype=np.float64)

    funds_py_total = timeit(lambda: total_funds_python(balances), number=repeats)
    funds_np_total = timeit(lambda: total_funds_numpy(balances_np), number=repeats)
    stats_py_total = timeit(lambda: transaction_statistics_python(amounts), number=repeats)
    stats_np_total = timeit(lambda: transaction_statistics_numpy(amounts_np), number=repeats)

    return {
        "total_funds_python_mean_s": funds_py_total / repeats,
        "total_funds_numpy_mean_s": funds_np_total / repeats,
        "tx_stats_python_mean_s": stats_py_total / repeats,
        "tx_stats_numpy_mean_s": stats_np_total / repeats,
    }


def _run_baseline_workload(
    balances: list[float],
    amounts: list[float],
    history: list[float],
    risk_sample: list[float],
) -> None:
    """Набір baseline-операцій Варіанта 4 для профілювання cProfile."""
    total_funds_python(balances)
    transaction_statistics_python(amounts)
    calculate_balance_from_history_python(10_000_000.0, history)
    calculate_risk_scores_sequential(risk_sample, iterations=100)


def _run_optimized_workload(
    balances: list[float],
    amounts: list[float],
    history: list[float],
    risk_sample: list[float],
) -> None:
    """Набір оптимізованих через NumPy операцій Варіанта 4 для профілювання cProfile."""
    total_funds_numpy(balances)
    transaction_statistics_numpy(amounts)
    calculate_balance_from_history_numpy(10_000_000.0, history)
    calculate_risk_scores_numpy(risk_sample, iterations=100)


def profile_with_cprofile(
    account_count: int = 100_000,
    operation_count: int = 500_000,
    risk_sample_size: int = 25_000,
) -> dict[str, str]:
    """Виконати cProfile до та після оптимізації й вивести ncalls/tottime/cumtime."""
    balances = generate_account_balances(count=account_count, seed=42)
    _, _, amounts = generate_operations(
        count=operation_count,
        account_count=account_count,
        seed=42,
    )
    history = generate_account_history(count=operation_count, seed=42)
    risk_sample = amounts[:risk_sample_size]

    baseline_profiler = cProfile.Profile()
    baseline_profiler.enable()
    _run_baseline_workload(balances, amounts, history, risk_sample)
    baseline_profiler.disable()

    baseline_stream = io.StringIO()
    baseline_stats = pstats.Stats(baseline_profiler, stream=baseline_stream)
    baseline_stats.sort_stats("cumulative")
    baseline_stats.print_stats(15)

    optimized_profiler = cProfile.Profile()
    optimized_profiler.enable()
    _run_optimized_workload(balances, amounts, history, risk_sample)
    optimized_profiler.disable()

    optimized_stream = io.StringIO()
    optimized_stats = pstats.Stats(optimized_profiler, stream=optimized_stream)
    optimized_stats.sort_stats("cumulative")
    optimized_stats.print_stats(15)

    return {
        "baseline_report": baseline_stream.getvalue(),
        "optimized_report": optimized_stream.getvalue(),
    }


def profile_memory_with_tracemalloc(
    account_count: int = 100_000,
    operation_count: int = 500_000,
) -> dict[str, Any]:
    """Проаналізувати використання пам'яті та топ рядків алокації через tracemalloc."""
    tracemalloc.start()
    balances = generate_account_balances(count=account_count, seed=42)
    _, _, amounts = generate_operations(
        count=operation_count,
        account_count=account_count,
        seed=42,
    )
    py_stats = transaction_statistics_python(amounts)
    py_current, py_peak = tracemalloc.get_traced_memory()
    snapshot = tracemalloc.take_snapshot()
    top_lines = [str(stat) for stat in snapshot.statistics("lineno")[:10]]
    tracemalloc.stop()

    tracemalloc.start()
    amounts_np = np.asarray(amounts, dtype=np.float64)
    np_stats = transaction_statistics_numpy(amounts_np)
    np_current, np_peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    del balances, amounts, amounts_np
    return {
        "python_current_mb": py_current / (1024 * 1024),
        "python_peak_mb": py_peak / (1024 * 1024),
        "numpy_current_mb": np_current / (1024 * 1024),
        "numpy_peak_mb": np_peak / (1024 * 1024),
        "top_allocations": top_lines,
        "stats_match": abs(py_stats["std"] - np_stats["std"]) < 1e-9,
    }


def run_full_profiling() -> None:
    """Запустити timeit, cProfile та tracemalloc для банківської аналітики."""
    print("=== 1. timeit (середній час за 5 повторів) ===")
    timings = run_timeit_comparison()
    for name, value in timings.items():
        print(f"{name:32} {value:.6f} s")

    print("\n=== 2. cProfile ДО оптимізації (baseline) ===")
    cprofile_reports = profile_with_cprofile()
    print(cprofile_reports["baseline_report"])

    print("=== 3. cProfile ПІСЛЯ оптимізації (NumPy) ===")
    print(cprofile_reports["optimized_report"])

    print("=== 4. tracemalloc аналіз пам'яті ===")
    mem = profile_memory_with_tracemalloc()
    print(f"Python dataset + stats Current: {mem['python_current_mb']:.2f} MB")
    print(f"Python dataset + stats Peak:    {mem['python_peak_mb']:.2f} MB")
    print(f"NumPy array + stats Current:    {mem['numpy_current_mb']:.2f} MB")
    print(f"NumPy array + stats Peak:       {mem['numpy_peak_mb']:.2f} MB")
    print("Топ-10 джерел алокації пам'яті (lineno):")
    for line in mem["top_allocations"]:
        print(" ", line)


if __name__ == "__main__":
    run_full_profiling()
