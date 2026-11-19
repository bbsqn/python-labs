"""Базові утиліти бенчмаркінгу, вимірювання пам'яті, збереження CSV та графіків."""

from __future__ import annotations

import csv
import tracemalloc
from collections.abc import Callable
from pathlib import Path
from statistics import mean, median
from time import perf_counter
from typing import Any

import matplotlib
import matplotlib.pyplot as plt

matplotlib.use("Agg")


def benchmark(
    name: str,
    function: Callable[..., Any],
    *args: Any,
) -> tuple[str, float, Any]:
    """Виміряти час одного запуску функції за допомогою perf_counter."""
    start = perf_counter()
    result = function(*args)
    elapsed = perf_counter() - start
    print(f"{name:28}{elapsed:10.6f} s")
    return name, elapsed, result


def benchmark_repeated(
    function: Callable[..., Any],
    *args: Any,
    repeats: int = 5,
    warmup: bool = True,
) -> tuple[list[float], float, float, Any]:
    """Виконати багаторазовий запуск функції та повернути часи, mean, median і результат."""
    if warmup:
        function(*args)
    times: list[float] = []
    result: Any = None
    for _ in range(repeats):
        start = perf_counter()
        result = function(*args)
        elapsed = perf_counter() - start
        times.append(elapsed)
    return times, mean(times), median(times), result


def measure_peak_memory_mb(
    function: Callable[..., Any],
    *args: Any,
) -> float:
    """Виміряти пікове використання Python-allocated memory (MB) через tracemalloc."""
    tracemalloc.start()
    function(*args)
    _, peak_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return peak_bytes / (1024 * 1024)


def calculate_speedup(
    baseline: float,
    optimized: float,
) -> float:
    """Обчислити коефіцієнт прискорення: baseline / optimized."""
    if optimized <= 0.0:
        return 0.0
    return baseline / optimized


def save_results_csv(
    rows: list[dict[str, Any]],
    output_path: Path,
) -> None:
    """Зберегти результати експериментів у CSV-файл."""
    if not rows:
        return
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys())
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def generate_benchmark_charts(
    summary_rows: list[dict[str, Any]],
    workers_rows: list[dict[str, Any]],
    output_dir: Path,
) -> tuple[Path, Path, Path]:
    """Побудувати графіки execution time, speedup та scaling за кількістю workers."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Execution time comparison (на найбільшому dataset)
    max_size = max(int(row["data_size"]) for row in summary_rows if str(row["data_size"]).isdigit())
    subset = [
        row
        for row in summary_rows
        if str(row["data_size"]) == str(max_size)
    ]
    methods = [str(row["experiment"]) for row in subset]
    mean_times = [float(row["mean_time_s"]) for row in subset]
    speedups = [float(row["speedup"]) for row in subset]

    exec_chart_path = output_dir / "execution_time_chart.png"
    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=150)
    colors = ["#4a5568", "#d97706", "#2563eb", "#059669"]
    bars = ax.bar(methods, mean_times, color=colors[: len(methods)], width=0.55)
    ax.set_title(f"Порівняння часу виконання (dataset = {max_size:,} операцій)")
    ax.set_ylabel("Середній час виконання, s")
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    for bar, val in zip(bars, mean_times):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            f"{val:.4f}s",
            ha="center",
            va="bottom",
            fontsize=9,
        )
    fig.tight_layout()
    fig.savefig(exec_chart_path)
    plt.close(fig)

    # 2. Speedup comparison
    speedup_chart_path = output_dir / "speedup_chart.png"
    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=150)
    bars = ax.bar(methods, speedups, color=colors[: len(methods)], width=0.55)
    ax.axhline(1.0, color="#6b7280", linestyle="--", linewidth=1, label="Baseline (1.0x)")
    ax.set_title(f"Коефіцієнт прискорення Speedup (dataset = {max_size:,} операцій)")
    ax.set_ylabel("Speedup (x)")
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    ax.legend()
    for bar, val in zip(bars, speedups):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            f"{val:.2f}x",
            ha="center",
            va="bottom",
            fontsize=9,
        )
    fig.tight_layout()
    fig.savefig(speedup_chart_path)
    plt.close(fig)

    # 3. Workers scaling chart (ThreadPool vs ProcessPool)
    workers_chart_path = output_dir / "workers_scaling_chart.png"
    worker_counts = [int(row["workers"]) for row in workers_rows]
    thread_times = [float(row["thread_pool_s"]) for row in workers_rows]
    process_times = [float(row["process_pool_s"]) for row in workers_rows]
    process_speedups = [float(row["process_speedup"]) for row in workers_rows]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.5, 4.2), dpi=150)
    ax1.plot(
        worker_counts,
        thread_times,
        marker="o",
        linewidth=2,
        color="#d97706",
        label="ThreadPool",
    )
    ax1.plot(
        worker_counts,
        process_times,
        marker="s",
        linewidth=2,
        color="#2563eb",
        label="ProcessPool",
    )
    ax1.set_title("Час виконання vs Кількість workers")
    ax1.set_xlabel("Workers")
    ax1.set_ylabel("Середній час, s")
    ax1.set_xticks(worker_counts)
    ax1.grid(True, linestyle="--", alpha=0.4)
    ax1.legend()

    ax2.plot(
        worker_counts,
        process_speedups,
        marker="s",
        linewidth=2,
        color="#059669",
        label="ProcessPool Speedup",
    )
    ax2.axhline(1.0, color="#6b7280", linestyle="--", linewidth=1)
    ax2.set_title("Масштабування Speedup (ProcessPool)")
    ax2.set_xlabel("Workers")
    ax2.set_ylabel("Speedup (x)")
    ax2.set_xticks(worker_counts)
    ax2.grid(True, linestyle="--", alpha=0.4)
    for x_val, y_val in zip(worker_counts, process_speedups):
        ax2.annotate(
            f"{y_val:.2f}x",
            (x_val, y_val),
            textcoords="offset points",
            xytext=(0, 6),
            ha="center",
            fontsize=8,
        )
    ax2.legend()

    fig.tight_layout()
    fig.savefig(workers_chart_path)
    plt.close(fig)

    return exec_chart_path, speedup_chart_path, workers_chart_path
