"""Аналітика банківської системи: генерація даних, baseline, NumPy та caching."""

from __future__ import annotations

import csv
import math
import random
from functools import _lru_cache_wrapper, lru_cache
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
from numpy.typing import NDArray

from .exceptions import InsufficientFundsError, InvalidAmountError

if TYPE_CHECKING:
    from functools import _CacheInfo

OPERATION_TYPES: tuple[str, ...] = (
    "deposit",
    "withdraw",
    "transfer_in",
    "transfer_out",
)


def generate_account_balances(
    count: int = 100_000,
    seed: int = 42,
) -> list[float]:
    """Згенерувати реалістичні залишки для заданої кількості банківських рахунків."""
    if count <= 0:
        raise ValueError("Кількість рахунків повинна бути додатною.")
    rng = random.Random(seed)
    return [round(rng.uniform(100.0, 50_000.0), 2) for _ in range(count)]


def generate_operations(
    count: int = 500_000,
    account_count: int = 100_000,
    seed: int = 42,
) -> tuple[list[int], list[str], list[float]]:
    """Згенерувати масив банківських операцій (account_id, тип операції, сума)."""
    if count <= 0 or account_count <= 0:
        raise ValueError("Кількість операцій та рахунків повинна бути додатною.")
    rng = random.Random(seed)
    account_ids: list[int] = [rng.randrange(1, account_count + 1) for _ in range(count)]
    op_types: list[str] = [rng.choice(OPERATION_TYPES) for _ in range(count)]
    amounts: list[float] = [round(rng.uniform(10.0, 5_000.0), 2) for _ in range(count)]
    return account_ids, op_types, amounts


def generate_account_history(
    count: int = 500_000,
    initial_balance: float = 10_000_000.0,
    seed: int = 42,
) -> list[float]:
    """Згенерувати велику історію знакових операцій (+надходження / -списання)."""
    if count <= 0:
        raise ValueError("Кількість операцій повинна бути додатною.")
    if initial_balance < 0:
        raise InsufficientFundsError("Початковий баланс не може бути від'ємним.")

    rng = random.Random(seed)
    balance = initial_balance
    history: list[float] = []
    for _ in range(count):
        amount = round(rng.uniform(10.0, 500.0), 2)
        if balance >= amount and rng.random() < 0.48:
            signed = -amount
        else:
            signed = amount
        balance = round(balance + signed, 2)
        history.append(signed)
    return history


def generate_operation_log_files(
    output_dir: Path,
    total_operations: int = 200_000,
    file_count: int = 8,
    account_count: int = 100_000,
    seed: int = 42,
) -> list[Path]:
    """Записати кілька CSV-журналів банківських операцій для I/O-bound експерименту."""
    if total_operations <= 0 or file_count <= 0:
        raise ValueError("Кількість операцій і файлів повинна бути додатною.")

    output_dir.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)
    per_file = total_operations // file_count
    remainder = total_operations % file_count
    paths: list[Path] = []

    for idx in range(file_count):
        file_ops = per_file + (1 if idx < remainder else 0)
        file_path = output_dir / f"operations_log_{idx + 1:02d}.csv"
        with file_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["account_id", "operation_type", "amount"])
            for _ in range(file_ops):
                writer.writerow(
                    [
                        rng.randrange(1, account_count + 1),
                        rng.choice(OPERATION_TYPES),
                        round(rng.uniform(10.0, 5_000.0), 2),
                    ]
                )
        paths.append(file_path)
    return paths


def total_funds_python(balances: list[float]) -> float:
    """Обчислити загальну суму коштів на всіх рахунках циклом Python (baseline)."""
    total = 0.0
    for balance in balances:
        total += balance
    return round(total, 2)


def total_funds_numpy(balances: list[float] | NDArray[np.float64]) -> float:
    """Обчислити загальну суму коштів на всіх рахунках за допомогою NumPy."""
    array = np.asarray(balances, dtype=np.float64)
    return round(float(np.sum(array)), 2)


def transaction_statistics_python(amounts: list[float]) -> dict[str, float]:
    """Обчислити оборот і статистику транзакцій на чистих циклах Python (baseline)."""
    count = len(amounts)
    if count == 0:
        raise ValueError("Список транзакцій порожній.")

    turnover = 0.0
    minimum = amounts[0]
    maximum = amounts[0]
    for value in amounts:
        turnover += value
        if value < minimum:
            minimum = value
        if value > maximum:
            maximum = value

    average = turnover / count
    squared_diff_sum = 0.0
    for value in amounts:
        diff = value - average
        squared_diff_sum += diff * diff
    std = math.sqrt(squared_diff_sum / count)

    return {
        "count": float(count),
        "turnover": turnover,
        "average": average,
        "minimum": minimum,
        "maximum": maximum,
        "std": std,
    }


def transaction_statistics_numpy(
    amounts: list[float] | NDArray[np.float64],
) -> dict[str, float]:
    """Векторизований розрахунок обороту та статистики транзакцій засобами NumPy."""
    array = np.asarray(amounts, dtype=np.float64)
    if array.size == 0:
        raise ValueError("Список транзакцій порожній.")

    return {
        "count": float(array.size),
        "turnover": float(array.sum()),
        "average": float(array.mean()),
        "minimum": float(array.min()),
        "maximum": float(array.max()),
        "std": float(array.std()),
    }


def calculate_balance_from_history_python(
    initial_balance: float,
    signed_amounts: list[float],
) -> dict[str, float]:
    """Розрахувати баланс, оборот і потоки за великою історією операцій у циклі Python."""
    if initial_balance < 0:
        raise InsufficientFundsError(
            f"Від'ємний початковий баланс заборонено: {initial_balance:.2f}"
        )

    balance = float(initial_balance)
    turnover = 0.0
    total_inflow = 0.0
    total_outflow = 0.0

    for delta in signed_amounts:
        balance += delta
        if balance < -1e-9:
            raise InsufficientFundsError(
                f"Баланс не може бути від'ємним під час розрахунку історії: {balance:.2f}"
            )
        if delta >= 0:
            total_inflow += delta
            turnover += delta
        else:
            out = -delta
            total_outflow += out
            turnover += out

    return {
        "final_balance": round(balance, 2),
        "turnover": round(turnover, 2),
        "total_inflow": round(total_inflow, 2),
        "total_outflow": round(total_outflow, 2),
    }


def calculate_balance_from_history_numpy(
    initial_balance: float,
    signed_amounts: list[float] | NDArray[np.float64],
) -> dict[str, float]:
    """Векторизований розрахунок балансу й обороту за історією операцій через NumPy."""
    if initial_balance < 0:
        raise InsufficientFundsError(
            f"Від'ємний початковий баланс заборонено: {initial_balance:.2f}"
        )

    array = np.asarray(signed_amounts, dtype=np.float64)
    if array.size == 0:
        return {
            "final_balance": round(float(initial_balance), 2),
            "turnover": 0.0,
            "total_inflow": 0.0,
            "total_outflow": 0.0,
        }

    running_balances = initial_balance + np.cumsum(array)
    if bool(np.any(running_balances < -1e-9)):
        min_balance = float(np.min(running_balances))
        raise InsufficientFundsError(
            f"Баланс не може бути від'ємним під час розрахунку історії: {min_balance:.2f}"
        )

    total_inflow = float(np.sum(np.maximum(array, 0.0)))
    total_outflow = float(np.sum(np.abs(np.minimum(array, 0.0))))
    turnover = float(np.sum(np.abs(array)))
    final_balance = float(running_balances[-1])

    return {
        "final_balance": round(final_balance, 2),
        "turnover": round(turnover, 2),
        "total_inflow": round(total_inflow, 2),
        "total_outflow": round(total_outflow, 2),
    }


def transaction_risk_score(
    amount: float,
    iterations: int = 100,
) -> float:
    """CPU-bound функція нелінійного скорингу окремої транзакції."""
    value = amount
    for _ in range(iterations):
        value = (
            math.sin(value) ** 2
            + math.cos(value) ** 2
            + math.sqrt(abs(value) + 1.0)
        )
    return value


def calculate_risk_scores_sequential(
    amounts: list[float],
    iterations: int = 100,
) -> list[float]:
    """Послідовний CPU-bound розрахунок скорингу транзакцій."""
    return [transaction_risk_score(amount, iterations=iterations) for amount in amounts]


def calculate_risk_scores_numpy(
    amounts: list[float] | NDArray[np.float64],
    iterations: int = 100,
) -> NDArray[np.float64]:
    """Векторизований розрахунок скорингу транзакцій через NumPy."""
    values = np.asarray(amounts, dtype=np.float64).copy()
    for _ in range(iterations):
        values = (
            np.sin(values) ** 2
            + np.cos(values) ** 2
            + np.sqrt(np.abs(values) + 1.0)
        )
    return values


class BankAnalyticsLedger:
    """Реєстр рахунків із кешованою статистикою (@lru_cache) та cache invalidation."""

    def __init__(self, maxsize: int = 256) -> None:
        self._balances: dict[int, float] = {}
        self._histories: dict[int, list[float]] = {}
        self._versions: dict[int, int] = {}
        self._cached_stats: _lru_cache_wrapper[dict[str, float]] = lru_cache(
            maxsize=maxsize
        )(self._compute_account_statistics)

    def register_account(
        self,
        account_id: int,
        initial_balance: float = 0.0,
        operations: list[float] | None = None,
    ) -> None:
        """Зареєструвати рахунок з початковим балансом та списком сум операцій."""
        if initial_balance < 0:
            raise InsufficientFundsError(
                f"Від'ємний баланс рахунку заборонено: {initial_balance:.2f}"
            )
        self._balances[account_id] = round(initial_balance, 2)
        self._histories[account_id] = list(operations) if operations is not None else []
        self._versions[account_id] = 1

    def add_operation(
        self,
        account_id: int,
        operation_type: str,
        amount: float,
    ) -> float:
        """Додати операцію (поповнення/списання) та виконати invalidation кешу рахунку."""
        if amount <= 0:
            raise InvalidAmountError(
                f"Сума операції повинна бути додатною, отримано: {amount:.2f}"
            )
        if account_id not in self._balances:
            raise KeyError(f"Рахунок id={account_id} не знайдено.")

        current_balance = self._balances[account_id]
        if operation_type in ("withdraw", "transfer_out"):
            if current_balance < amount:
                raise InsufficientFundsError(
                    f"Недостатньо коштів на рахунку {account_id}: "
                    f"доступно {current_balance:.2f}, запитано {amount:.2f}"
                )
            self._balances[account_id] = round(current_balance - amount, 2)
        else:
            self._balances[account_id] = round(current_balance + amount, 2)

        self._histories[account_id].append(round(amount, 2))
        self._versions[account_id] += 1
        return self._balances[account_id]

    def get_balance(self, account_id: int) -> float:
        """Отримати поточний баланс рахунку."""
        if account_id not in self._balances:
            raise KeyError(f"Рахунок id={account_id} не знайдено.")
        return self._balances[account_id]

    def get_version(self, account_id: int) -> int:
        """Отримати поточну версію даних рахунку (ключ інвалідації кешу)."""
        if account_id not in self._versions:
            raise KeyError(f"Рахунок id={account_id} не знайдено.")
        return self._versions[account_id]

    def _compute_account_statistics(
        self,
        account_id: int,
        _version: int,
    ) -> dict[str, float]:
        """Обчислити статистику транзакцій рахунку (викликається при cache miss)."""
        history = self._histories[account_id]
        stats = transaction_statistics_python(history)
        stats["current_balance"] = self._balances[account_id]
        return stats

    def get_account_statistics(self, account_id: int) -> dict[str, float]:
        """Отримати статистику транзакцій рахунку з використанням @lru_cache."""
        if account_id not in self._histories:
            raise KeyError(f"Рахунок id={account_id} не знайдено.")
        version = self._versions[account_id]
        return self._cached_stats(account_id, version)

    def cache_info(self) -> _CacheInfo:
        """Повернути метрики hits/misses/maxsize/currsize кешу."""
        return self._cached_stats.cache_info()

    def cache_clear(self) -> None:
        """Повністю очистити кеш статистики."""
        self._cached_stats.cache_clear()
