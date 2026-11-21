"""Бенчмарк процесів: масштабування workers = 1, 2, 4, 8 та порівняння chunksize."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "src"))
sys.path.insert(0, str(ROOT_DIR / "benchmarks"))

from benchmark import (  # noqa: E402
    benchmark_repeated,
    calculate_speedup,
    save_results_csv,
)

from bank_account_service.analytics import (  # noqa: E402
    calculate_risk_scores_sequential,
    generate_operations,
)
from bank_account_service.parallel import (  # noqa: E402
    calculate_risk_scores_manual_processes,
    calculate_risk_scores_processes,
    calculate_risk_scores_threads,
)


def run_workers_scaling_benchmark(
    sample_size: int = 100_000,
) -> list[dict[str, object]]:
    """Дослідити scaling для workers = 1, 2, 4, 8 (ThreadPool vs ProcessPool)."""
    _, _, amounts = generate_operations(count=sample_size, account_count=100_000, seed=42)
    iterations = 100

    _, seq_mean, _, seq_res = benchmark_repeated(
        calculate_risk_scores_sequential,
        amounts,
        iterations,
        repeats=5,
    )

    rows: list[dict[str, object]] = []
    for workers in (1, 2, 4, 8):
        _, thr_mean, _, thr_res = benchmark_repeated(
            calculate_risk_scores_threads,
            amounts,
            workers,
            iterations,
            repeats=5,
        )
        _, proc_mean, _, proc_res = benchmark_repeated(
            calculate_risk_scores_processes,
            amounts,
            workers,
            2500,
            iterations,
            repeats=5,
        )
        assert abs(seq_res[0] - thr_res[0]) < 1e-12
        assert abs(seq_res[0] - proc_res[0]) < 1e-12

        rows.append(
            {
                "workers": workers,
                "sequential_s": round(seq_mean, 6),
                "thread_pool_s": round(thr_mean, 6),
                "process_pool_s": round(proc_mean, 6),
                "thread_speedup": round(calculate_speedup(seq_mean, thr_mean), 2),
                "process_speedup": round(calculate_speedup(seq_mean, proc_mean), 2),
            }
        )

    # Перевірка прямого multiprocessing.Process на піднаборі
    manual_res = calculate_risk_scores_manual_processes(amounts[:10_000], workers=4, iterations=100)
    assert abs(manual_res[0] - seq_res[0]) < 1e-12

    # Дослідження впливу chunksize для ProcessPoolExecutor (workers=4)
    print(f"=== Дослідження scaling workers (CPU-bound, {sample_size:,} операцій) ===")
    print(f"Sequential baseline: {seq_mean:.6f} s")
    for row in rows:
        print(
            f"workers={row['workers']} | "
            f"ThreadPool={row['thread_pool_s']:.6f}s ({row['thread_speedup']:.2f}x) | "
            f"ProcessPool={row['process_pool_s']:.6f}s ({row['process_speedup']:.2f}x)"
        )

    print("\n=== Вплив chunksize (ProcessPoolExecutor, workers=4) ===")
    for chunksize in (100, 1000, 5000):
        _, c_mean, _, _ = benchmark_repeated(
            calculate_risk_scores_processes,
            amounts,
            4,
            chunksize,
            iterations,
            repeats=3,
        )
        speedup_val = calculate_speedup(seq_mean, c_mean)
        print(f"chunksize={chunksize:5d} -> {c_mean:.6f} s ({speedup_val:.2f}x)")

    results_path = ROOT_DIR / "benchmarks" / "results" / "workers_scaling.csv"
    save_results_csv(rows, results_path)
    return rows


if __name__ == "__main__":
    run_workers_scaling_benchmark()
