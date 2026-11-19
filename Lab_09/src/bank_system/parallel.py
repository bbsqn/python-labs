"""Паралельне та конкурентне виконання: threading, multiprocessing, executors і Lock."""

from __future__ import annotations

import csv
import math
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from itertools import repeat
from multiprocessing import Process, Queue
from pathlib import Path
from threading import Lock, Thread

from .analytics import transaction_risk_score
from .exceptions import InsufficientFundsError, InvalidAmountError


def _chunk_list(values: list[float], num_chunks: int) -> list[list[float]]:
    """Розбити список на непусті підсписки для розподілу між workers."""
    if not values:
        return []
    actual_chunks = max(1, min(num_chunks, len(values)))
    chunk_size = math.ceil(len(values) / actual_chunks)
    return [values[i : i + chunk_size] for i in range(0, len(values), chunk_size)]


def _score_chunk(args: tuple[list[float], int]) -> list[float]:
    """Обробити пакет значень у потоці або процесі."""
    chunk, iterations = args
    return [transaction_risk_score(amount, iterations=iterations) for amount in chunk]


def _partial_stats_worker(
    chunk: list[float],
) -> tuple[int, float, float, float, float]:
    """Обчислити часткову статистику фрагмента (count, mean, m2, min, max) за алгоритмом Чана."""
    count = len(chunk)
    total = 0.0
    minimum = chunk[0]
    maximum = chunk[0]
    for value in chunk:
        total += value
        if value < minimum:
            minimum = value
        if value > maximum:
            maximum = value
    mean = total / count
    m2 = 0.0
    for value in chunk:
        diff = value - mean
        m2 += diff * diff
    return count, mean, m2, minimum, maximum


def _merge_partial_stats(
    partials: list[tuple[int, float, float, float, float]],
) -> dict[str, float]:
    """Об'єднати часткові статистики фрагментів без втрати точності (алгоритм Чана)."""
    total_count, mean_a, m2_a, min_val, max_val = partials[0]
    for count_b, mean_b, m2_b, min_b, max_b in partials[1:]:
        new_count = total_count + count_b
        delta = mean_b - mean_a
        mean_a = (total_count * mean_a + count_b * mean_b) / new_count
        m2_a = m2_a + m2_b + (delta * delta) * (total_count * count_b / new_count)
        total_count = new_count
        if min_b < min_val:
            min_val = min_b
        if max_b > max_val:
            max_val = max_b

    turnover = mean_a * total_count
    std = math.sqrt(m2_a / total_count)
    return {
        "count": float(total_count),
        "turnover": turnover,
        "average": mean_a,
        "minimum": min_val,
        "maximum": max_val,
        "std": std,
    }


def _manual_process_worker(
    index: int,
    chunk: list[float],
    iterations: int,
    output_queue: Queue[tuple[int, list[float]]],
) -> None:
    """Функція-воркер верхнього рівня для прямого запуску multiprocessing.Process."""
    scores = [transaction_risk_score(amount, iterations=iterations) for amount in chunk]
    output_queue.put((index, scores))


def load_operation_log_csv(path: Path) -> list[float]:
    """Прочитати CSV-журнал банківських операцій та повернути список сум (I/O-bound)."""
    amounts: list[float] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        next(reader, None)  # Пропустити заголовок CSV
        for row in reader:
            if len(row) >= 3:
                amounts.append(float(row[2]))
    return amounts


def load_operation_logs_sequential(paths: list[Path]) -> list[list[float]]:
    """Послідовно прочитати набір CSV-журналів операцій."""
    return [load_operation_log_csv(path) for path in paths]


def load_operation_logs_threadpool(
    paths: list[Path],
    workers: int = 8,
) -> list[list[float]]:
    """Паралельно прочитати набір CSV-журналів операцій через ThreadPoolExecutor."""
    if not paths:
        return []
    with ThreadPoolExecutor(max_workers=workers) as executor:
        return list(executor.map(load_operation_log_csv, paths))


def read_logs_manual_threads(paths: list[Path]) -> tuple[list[list[float]], int]:
    """Приклад прямого використання threading.Thread і Lock для читання журналів."""
    results: list[list[float]] = [[] for _ in paths]
    processed_counter = 0
    counter_lock = Lock()

    def _worker(index: int, file_path: Path) -> None:
        nonlocal processed_counter
        loaded = load_operation_log_csv(file_path)
        results[index] = loaded
        with counter_lock:
            processed_counter += 1

    threads: list[Thread] = []
    for idx, path in enumerate(paths):
        thread = Thread(target=_worker, args=(idx, path))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    return results, processed_counter


def transaction_statistics_threads(
    amounts: list[float],
    workers: int = 4,
) -> dict[str, float]:
    """Обчислення статистики транзакцій через ThreadPoolExecutor."""
    if not amounts:
        raise ValueError("Список транзакцій порожній.")
    chunks = _chunk_list(amounts, workers * 2)
    with ThreadPoolExecutor(max_workers=workers) as executor:
        partials = list(executor.map(_partial_stats_worker, chunks))
    return _merge_partial_stats(partials)


def transaction_statistics_processes(
    amounts: list[float],
    workers: int = 4,
) -> dict[str, float]:
    """Обчислення статистики транзакцій через ProcessPoolExecutor."""
    if not amounts:
        raise ValueError("Список транзакцій порожній.")
    chunks = _chunk_list(amounts, workers * 2)
    with ProcessPoolExecutor(max_workers=workers) as executor:
        partials = list(executor.map(_partial_stats_worker, chunks))
    return _merge_partial_stats(partials)


def calculate_risk_scores_threads(
    amounts: list[float],
    workers: int = 4,
    iterations: int = 100,
) -> list[float]:
    """Обчислення скорингу транзакцій через ThreadPoolExecutor (демонстрація впливу GIL)."""
    if not amounts:
        return []
    chunks = _chunk_list(amounts, workers * 4)
    tasks = [(chunk, iterations) for chunk in chunks]
    with ThreadPoolExecutor(max_workers=workers) as executor:
        chunk_results = list(executor.map(_score_chunk, tasks))
    merged: list[float] = []
    for part in chunk_results:
        merged.extend(part)
    return merged


def calculate_risk_scores_processes(
    amounts: list[float],
    workers: int = 4,
    chunksize: int = 1000,
    iterations: int = 100,
) -> list[float]:
    """Паралельне обчислення скорингу транзакцій через ProcessPoolExecutor з chunksize."""
    if not amounts:
        return []
    with ProcessPoolExecutor(max_workers=workers) as executor:
        return list(
            executor.map(
                transaction_risk_score,
                amounts,
                repeat(iterations),
                chunksize=chunksize,
            )
        )


def calculate_risk_scores_manual_processes(
    amounts: list[float],
    workers: int = 4,
    iterations: int = 100,
) -> list[float]:
    """Приклад прямого створення процесів через multiprocessing.Process (start/join)."""
    if not amounts:
        return []
    chunks = _chunk_list(amounts, workers)
    output_queue: Queue[tuple[int, list[float]]] = Queue()
    processes: list[Process] = []

    for idx, chunk in enumerate(chunks):
        process = Process(
            target=_manual_process_worker,
            args=(idx, chunk, iterations, output_queue),
        )
        processes.append(process)
        process.start()

    ordered_results: list[list[float]] = [[] for _ in chunks]
    for _ in range(len(chunks)):
        idx, scores = output_queue.get()
        ordered_results[idx] = scores

    for process in processes:
        process.join()

    merged: list[float] = []
    for part in ordered_results:
        merged.extend(part)
    return merged


class SharedAccountState:
    """Спільний стан банківського рахунку в пам'яті для демонстрації race condition і Lock."""

    def __init__(self, initial_balance: float) -> None:
        if initial_balance < 0:
            raise InsufficientFundsError(
                f"Від'ємний баланс рахунку заборонено: {initial_balance:.2f}"
            )
        self.balance: float = round(initial_balance, 2)
        self.processed_operations: int = 0
        self._lock = Lock()

    def deposit_unsafe(self, amount: float) -> None:
        """Поповнення без синхронізації (схильне до race condition)."""
        if amount <= 0:
            raise InvalidAmountError(f"Сума повинна бути додатною: {amount:.2f}")
        current = self.balance
        ops = self.processed_operations
        time.sleep(0)
        self.balance = round(current + amount, 2)
        self.processed_operations = ops + 1

    def withdraw_unsafe(self, amount: float) -> None:
        """Списання без синхронізації (схильне до race condition)."""
        if amount <= 0:
            raise InvalidAmountError(f"Сума повинна бути додатною: {amount:.2f}")
        current = self.balance
        if current < amount:
            raise InsufficientFundsError(
                f"Недостатньо коштів: доступно {current:.2f}, запитано {amount:.2f}"
            )
        ops = self.processed_operations
        time.sleep(0)
        self.balance = round(current - amount, 2)
        self.processed_operations = ops + 1

    def deposit_safe(self, amount: float) -> None:
        """Поповнення із синхронізацією критичної секції через Lock."""
        if amount <= 0:
            raise InvalidAmountError(f"Сума повинна бути додатною: {amount:.2f}")
        with self._lock:
            self.balance = round(self.balance + amount, 2)
            self.processed_operations += 1

    def withdraw_safe(self, amount: float) -> None:
        """Списання із синхронізацією критичної секції через Lock та забороною мінусу."""
        if amount <= 0:
            raise InvalidAmountError(f"Сума повинна бути додатною: {amount:.2f}")
        with self._lock:
            if self.balance < amount:
                raise InsufficientFundsError(
                    f"Недостатньо коштів: доступно {self.balance:.2f}, запитано {amount:.2f}"
                )
            self.balance = round(self.balance - amount, 2)
            self.processed_operations += 1


def run_concurrent_account_simulation(
    initial_balance: float = 10_000.0,
    operations_per_thread: int = 500,
    deposit_amount: float = 100.0,
    withdrawal_amount: float = 40.0,
    threads_count: int = 4,
    use_lock: bool = True,
) -> dict[str, float | int | bool]:
    """Змоделювати конкурентні поповнення/списання з Lock або без нього."""
    account = SharedAccountState(initial_balance=initial_balance)
    errors: list[Exception] = []
    errors_lock = Lock()

    def _worker() -> None:
        try:
            for _ in range(operations_per_thread):
                if use_lock:
                    account.deposit_safe(deposit_amount)
                    account.withdraw_safe(withdrawal_amount)
                else:
                    account.deposit_unsafe(deposit_amount)
                    account.withdraw_unsafe(withdrawal_amount)
        except Exception as exc:  # pragma: no cover - діагностика збоїв конкурентності
            with errors_lock:
                errors.append(exc)

    threads: list[Thread] = []
    for _ in range(threads_count):
        thread = Thread(target=_worker)
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    expected_operations = threads_count * operations_per_thread * 2
    net_per_pair = deposit_amount - withdrawal_amount
    expected_balance = round(
        initial_balance + (threads_count * operations_per_thread * net_per_pair),
        2,
    )

    return {
        "use_lock": use_lock,
        "threads_count": threads_count,
        "expected_balance": expected_balance,
        "actual_balance": account.balance,
        "expected_operations": expected_operations,
        "actual_operations": account.processed_operations,
        "errors_count": len(errors),
        "is_consistent": (
            len(errors) == 0
            and abs(account.balance - expected_balance) < 1e-6
            and account.processed_operations == expected_operations
        ),
    }
