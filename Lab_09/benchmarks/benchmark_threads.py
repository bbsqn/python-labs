"""Бенчмарк потоків: I/O-bound читання журналів (ThreadPoolExecutor) та Lock-синхронізація."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "src"))
sys.path.insert(0, str(ROOT_DIR / "benchmarks"))

from benchmark import (  # noqa: E402
    benchmark_repeated,
    calculate_speedup,
    measure_peak_memory_mb,
)

from bank_system.analytics import generate_operation_log_files  # noqa: E402
from bank_system.parallel import (  # noqa: E402
    load_operation_logs_sequential,
    load_operation_logs_threadpool,
    read_logs_manual_threads,
    run_concurrent_account_simulation,
)


def run_threads_benchmark() -> dict[str, object]:
    """Дослідити ThreadPoolExecutor на I/O-bound задачі та Lock-синхронізацію."""
    logs_dir = ROOT_DIR / "benchmarks" / "results" / "tmp_logs"
    try:
        paths = generate_operation_log_files(
            output_dir=logs_dir,
            total_operations=200_000,
            file_count=8,
            account_count=100_000,
            seed=42,
        )

        _, seq_mean, _, seq_res = benchmark_repeated(
            load_operation_logs_sequential,
            paths,
            repeats=5,
        )
        seq_mem = measure_peak_memory_mb(load_operation_logs_sequential, paths)

        io_rows: list[dict[str, object]] = [
            {
                "method": "Sequential I/O",
                "workers": 1,
                "mean_time_s": round(seq_mean, 6),
                "peak_memory_mb": round(seq_mem, 4),
                "speedup": 1.0,
            }
        ]

        for workers in (2, 4, 8):
            _, thr_mean, _, thr_res = benchmark_repeated(
                load_operation_logs_threadpool,
                paths,
                workers,
                repeats=5,
            )
            thr_mem = measure_peak_memory_mb(load_operation_logs_threadpool, paths, workers)
            assert sum(len(part) for part in thr_res) == sum(len(part) for part in seq_res)
            io_rows.append(
                {
                    "method": "ThreadPoolExecutor I/O",
                    "workers": workers,
                    "mean_time_s": round(thr_mean, 6),
                    "peak_memory_mb": round(thr_mem, 4),
                    "speedup": round(calculate_speedup(seq_mean, thr_mean), 2),
                }
            )

        manual_res, processed_count = read_logs_manual_threads(paths)
        assert processed_count == len(paths)
        assert sum(len(part) for part in manual_res) == 200_000

        print("=== I/O-bound читання 8 CSV-журналів (200 000 операцій) ===")
        for row in io_rows:
            print(
                f"{str(row['method']):24} workers={row['workers']} | "
                f"mean={row['mean_time_s']:.6f}s | mem={row['peak_memory_mb']:.2f} MB | "
                f"speedup={row['speedup']:.2f}x"
            )

        unsafe_sim = run_concurrent_account_simulation(
            initial_balance=10_000.0,
            operations_per_thread=500,
            deposit_amount=100.0,
            withdrawal_amount=40.0,
            threads_count=4,
            use_lock=False,
        )
        safe_sim = run_concurrent_account_simulation(
            initial_balance=10_000.0,
            operations_per_thread=500,
            deposit_amount=100.0,
            withdrawal_amount=40.0,
            threads_count=4,
            use_lock=True,
        )
        print("\n=== Демонстрація Race Condition та Synchronization через Lock ===")
        print("Без Lock:", unsafe_sim)
        print("Із Lock: ", safe_sim)

        return {
            "io_rows": io_rows,
            "unsafe_simulation": unsafe_sim,
            "safe_simulation": safe_sim,
        }
    finally:
        shutil.rmtree(logs_dir, ignore_errors=True)


if __name__ == "__main__":
    run_threads_benchmark()
