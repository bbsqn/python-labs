"""Бенчмарк порівняння Python list + loops та NumPy array + vectorization."""

from __future__ import annotations

import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "src"))
sys.path.insert(0, str(ROOT_DIR / "benchmarks"))

import numpy as np  # noqa: E402
from benchmark import (  # noqa: E402
    benchmark_repeated,
    calculate_speedup,
    measure_peak_memory_mb,
)

from bank_account_service.analytics import (  # noqa: E402
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


def run_numpy_benchmark() -> list[dict[str, object]]:
    """Порівняти Python loops і NumPy vectorization для банківських обчислень."""
    balances = generate_account_balances(count=100_000, seed=42)
    _, _, amounts = generate_operations(count=500_000, account_count=100_000, seed=42)
    history = generate_account_history(count=500_000, seed=42)

    balances_np = np.asarray(balances, dtype=np.float64)
    amounts_np = np.asarray(amounts, dtype=np.float64)
    history_np = np.asarray(history, dtype=np.float64)
    risk_sample = amounts[:100_000]
    risk_sample_np = np.asarray(risk_sample, dtype=np.float64)

    rows: list[dict[str, object]] = []

    cases: list[
        tuple[
            str,
            Callable[..., Any],
            tuple[Any, ...],
            Callable[..., Any],
            tuple[Any, ...],
        ]
    ] = [
        (
            "Загальна сума (100k рахунків)",
            total_funds_python,
            (balances,),
            total_funds_numpy,
            (balances_np,),
        ),
        (
            "Статистика транзакцій (500k)",
            transaction_statistics_python,
            (amounts,),
            transaction_statistics_numpy,
            (amounts_np,),
        ),
        (
            "Баланс з історії (500k)",
            calculate_balance_from_history_python,
            (10_000_000.0, history),
            calculate_balance_from_history_numpy,
            (10_000_000.0, history_np),
        ),
        (
            "Скоринг транзакцій (100k)",
            calculate_risk_scores_sequential,
            (risk_sample, 100),
            calculate_risk_scores_numpy,
            (risk_sample_np, 100),
        ),
    ]

    for label, py_fn, py_args, np_fn, np_args in cases:
        _, py_mean, _, py_res = benchmark_repeated(py_fn, *py_args, repeats=5)
        _, np_mean, _, np_res = benchmark_repeated(np_fn, *np_args, repeats=5)
        py_mem = measure_peak_memory_mb(py_fn, *py_args)
        np_mem = measure_peak_memory_mb(np_fn, *np_args)
        speedup = calculate_speedup(py_mean, np_mean)

        # Перевірка правильності
        if isinstance(py_res, float):
            assert abs(py_res - float(np_res)) < 1e-6
        elif isinstance(py_res, dict):
            key = "std" if "std" in py_res else "final_balance"
            assert abs(py_res[key] - float(np_res[key])) < 1e-6
        elif isinstance(py_res, list):
            assert abs(py_res[0] - float(np_res[0])) < 1e-9

        rows.append(
            {
                "operation": label,
                "python_mean_s": round(py_mean, 6),
                "numpy_mean_s": round(np_mean, 6),
                "python_peak_mb": round(py_mem, 4),
                "numpy_peak_mb": round(np_mem, 4),
                "speedup": round(speedup, 2),
            }
        )

    print("=== Python loops vs NumPy vectorization ===")
    for row in rows:
        print(
            f"{str(row['operation']):32} "
            f"Python={row['python_mean_s']:.6f}s ({row['python_peak_mb']:.2f} MB) | "
            f"NumPy={row['numpy_mean_s']:.6f}s ({row['numpy_peak_mb']:.2f} MB) | "
            f"Speedup={row['speedup']:.2f}x"
        )
    return rows


if __name__ == "__main__":
    run_numpy_benchmark()
