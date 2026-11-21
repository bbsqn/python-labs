"""Головний експериментальний бенчмарк: 3 розміри даних, 5 повторів, кешування та графіки."""

from __future__ import annotations

import math
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
    generate_benchmark_charts,
    measure_peak_memory_mb,
    save_results_csv,
)
from benchmark_processes import run_workers_scaling_benchmark  # noqa: E402

from bank_account_service.analytics import (  # noqa: E402
    BankAnalyticsLedger,
    calculate_risk_scores_numpy,
    calculate_risk_scores_sequential,
    generate_operations,
    transaction_statistics_numpy,
    transaction_statistics_python,
)
from bank_account_service.parallel import (  # noqa: E402
    calculate_risk_scores_processes,
    calculate_risk_scores_threads,
    transaction_statistics_processes,
    transaction_statistics_threads,
)


def _format_runs(runs: list[float]) -> dict[str, float]:
    return {f"run_{i + 1}": round(val, 6) for i, val in enumerate(runs)}


def run_statistics_benchmark() -> tuple[
    list[dict[str, object]],
    list[dict[str, object]],
    list[dict[str, object]],
]:
    """Виконати експерименти для 10 000, 100 000 та 500 000 операцій (по 5 повторів)."""
    dataset_sizes = (10_000, 100_000, 500_000)
    stats_rows: list[dict[str, object]] = []
    scoring_rows: list[dict[str, object]] = []

    for size in dataset_sizes:
        _, _, amounts = generate_operations(count=size, account_count=100_000, seed=42)
        amounts_np = np.asarray(amounts, dtype=np.float64)

        # 1. Статистика транзакцій і оборот
        stat_methods: list[tuple[str, str, Callable[..., Any], tuple[Any, ...]]] = [
            ("Baseline", "1", transaction_statistics_python, (amounts,)),
            ("Threads", "4", transaction_statistics_threads, (amounts, 4)),
            ("Processes", "4", transaction_statistics_processes, (amounts, 4)),
            ("NumPy", "-", transaction_statistics_numpy, (amounts_np,)),
        ]
        baseline_stat_mean = 0.0
        baseline_stat_res: dict[str, float] | None = None

        for exp_name, workers_lbl, stat_fn, stat_args in stat_methods:
            runs, mean_t, _, res = benchmark_repeated(stat_fn, *stat_args, repeats=5)
            peak_mb = measure_peak_memory_mb(stat_fn, *stat_args)
            if exp_name == "Baseline":
                baseline_stat_mean = mean_t
                baseline_stat_res = res
                speedup = 1.0
            else:
                speedup = calculate_speedup(baseline_stat_mean, mean_t)
                assert baseline_stat_res is not None
                assert math.isclose(
                    res["average"],
                    baseline_stat_res["average"],
                    rel_tol=1e-9,
                    abs_tol=1e-9,
                )
                assert math.isclose(
                    res["std"],
                    baseline_stat_res["std"],
                    rel_tol=1e-9,
                    abs_tol=1e-9,
                )
                assert math.isclose(
                    res["turnover"],
                    baseline_stat_res["turnover"],
                    rel_tol=1e-9,
                    abs_tol=1e-9,
                )

            row: dict[str, object] = {
                "experiment": exp_name,
                "data_size": size,
                "workers": workers_lbl,
                **_format_runs(runs),
                "mean_time_s": round(mean_t, 6),
                "peak_memory_mb": round(peak_mb, 4),
                "speedup": round(speedup, 2),
            }
            stats_rows.append(row)

        # 2. Важке CPU-bound обчислення (скоринг транзакцій)
        score_methods: list[tuple[str, str, Callable[..., Any], tuple[Any, ...]]] = [
            ("Baseline", "1", calculate_risk_scores_sequential, (amounts, 100)),
            ("Threads", "4", calculate_risk_scores_threads, (amounts, 4, 100)),
            ("Processes", "4", calculate_risk_scores_processes, (amounts, 4, 5000, 100)),
            ("NumPy", "-", calculate_risk_scores_numpy, (amounts_np, 100)),
        ]
        baseline_score_mean = 0.0
        baseline_score_res: list[float] | None = None

        for exp_name, workers_lbl, score_fn, score_args in score_methods:
            runs, mean_t, _, res = benchmark_repeated(score_fn, *score_args, repeats=5)
            peak_mb = measure_peak_memory_mb(score_fn, *score_args)
            if exp_name == "Baseline":
                baseline_score_mean = mean_t
                baseline_score_res = res
                speedup = 1.0
            else:
                speedup = calculate_speedup(baseline_score_mean, mean_t)
                assert baseline_score_res is not None
                assert abs(float(res[0]) - baseline_score_res[0]) < 1e-9
                assert abs(float(res[-1]) - baseline_score_res[-1]) < 1e-9

            row = {
                "experiment": exp_name,
                "data_size": size,
                "workers": workers_lbl,
                **_format_runs(runs),
                "mean_time_s": round(mean_t, 6),
                "peak_memory_mb": round(peak_mb, 4),
                "speedup": round(speedup, 2),
            }
            scoring_rows.append(row)

    # 3. Бенчмарк кешування (Cold vs Warm cache + Invalidation)
    _, _, cache_ops = generate_operations(count=100_000, account_count=100_000, seed=7)
    ledger = BankAnalyticsLedger(maxsize=128)
    ledger.register_account(account_id=1, initial_balance=100_000.0, operations=cache_ops)

    def _cold_call() -> dict[str, float]:
        ledger.cache_clear()
        return ledger.get_account_statistics(1)

    cold_runs, cold_mean, _, _ = benchmark_repeated(_cold_call, repeats=5)
    cold_mem = measure_peak_memory_mb(_cold_call)

    # Прогрів кешу перед warm-заміром
    ledger.get_account_statistics(1)
    warm_runs, warm_mean, _, _ = benchmark_repeated(ledger.get_account_statistics, 1, repeats=5)
    warm_mem = measure_peak_memory_mb(ledger.get_account_statistics, 1)

    # Перевірка cache invalidation після додавання нової операції
    before_count = ledger.get_account_statistics(1)["count"]
    ledger.add_operation(account_id=1, operation_type="deposit", amount=2500.0)
    after_count = ledger.get_account_statistics(1)["count"]
    assert after_count == before_count + 1.0
    cache_info = ledger.cache_info()

    cache_rows: list[dict[str, object]] = [
        {
            "experiment": "Cold cache (miss)",
            "data_size": 100_000,
            "workers": "1",
            **_format_runs(cold_runs),
            "mean_time_s": round(cold_mean, 6),
            "peak_memory_mb": round(cold_mem, 4),
            "speedup": 1.0,
        },
        {
            "experiment": "Warm cache (hit)",
            "data_size": 100_000,
            "workers": "-",
            **_format_runs(warm_runs),
            "mean_time_s": round(warm_mean, 6),
            "peak_memory_mb": round(warm_mem, 4),
            "speedup": round(calculate_speedup(cold_mean, warm_mean), 2),
        },
    ]

    results_dir = ROOT_DIR / "benchmarks" / "results"
    save_results_csv(stats_rows, results_dir / "benchmark_results.csv")
    save_results_csv(scoring_rows, results_dir / "scoring_results.csv")
    save_results_csv(cache_rows, results_dir / "cache_results.csv")

    print("=== 1. Статистика транзакцій (Python vs Threads vs Processes vs NumPy) ===")
    for row in stats_rows:
        print(
            f"size={row['data_size']:7} | {str(row['experiment']):10} | "
            f"workers={str(row['workers']):2} | mean={row['mean_time_s']:.6f}s | "
            f"mem={row['peak_memory_mb']:.4f} MB | speedup={row['speedup']:.2f}x"
        )

    print("\n=== 2. CPU-bound скоринг транзакцій (100 ітерацій на елемент) ===")
    for row in scoring_rows:
        print(
            f"size={row['data_size']:7} | {str(row['experiment']):10} | "
            f"workers={str(row['workers']):2} | mean={row['mean_time_s']:.6f}s | "
            f"mem={row['peak_memory_mb']:.4f} MB | speedup={row['speedup']:.2f}x"
        )

    print("\n=== 3. Caching (100 000 операцій) + Invalidation ===")
    for row in cache_rows:
        print(
            f"{str(row['experiment']):20} | mean={row['mean_time_s']:.6f}s | "
            f"mem={row['peak_memory_mb']:.4f} MB | speedup={row['speedup']:.2f}x"
        )
    print(f"CacheInfo після invalidation: {cache_info}")

    return stats_rows, scoring_rows, cache_rows


if __name__ == "__main__":
    _, scoring_rows, _ = run_statistics_benchmark()
    workers_rows = run_workers_scaling_benchmark(sample_size=100_000)
    charts = generate_benchmark_charts(
        summary_rows=scoring_rows,
        workers_rows=workers_rows,
        output_dir=ROOT_DIR / "benchmarks" / "results",
    )
    print("\nЗбережені графіки:", [str(p.name) for p in charts])
