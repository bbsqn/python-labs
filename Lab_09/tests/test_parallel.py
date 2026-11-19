"""Автоматичні тести правильності оптимізації, паралельності, Lock та caching."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from bank_system.analytics import (
    BankAnalyticsLedger,
    calculate_balance_from_history_numpy,
    calculate_balance_from_history_python,
    calculate_risk_scores_numpy,
    calculate_risk_scores_sequential,
    generate_account_balances,
    generate_account_history,
    generate_operation_log_files,
    generate_operations,
    total_funds_numpy,
    total_funds_python,
    transaction_statistics_numpy,
    transaction_statistics_python,
)
from bank_system.exceptions import InsufficientFundsError, InvalidAmountError
from bank_system.parallel import (
    SharedAccountState,
    calculate_risk_scores_manual_processes,
    calculate_risk_scores_processes,
    calculate_risk_scores_threads,
    load_operation_logs_sequential,
    load_operation_logs_threadpool,
    read_logs_manual_threads,
    run_concurrent_account_simulation,
    transaction_statistics_processes,
    transaction_statistics_threads,
)


def test_dataset_generation_volumes_variant4() -> None:
    """Перевірка генерації достатнього обсягу даних Варіанта 4 (100k рахунків, 500k операцій)."""
    balances = generate_account_balances(count=100_000, seed=42)
    account_ids, op_types, amounts = generate_operations(
        count=500_000,
        account_count=100_000,
        seed=42,
    )
    assert len(balances) == 100_000
    assert len(account_ids) == 500_000
    assert len(op_types) == 500_000
    assert len(amounts) == 500_000
    assert min(balances) >= 100.0
    assert min(amounts) >= 10.0


def test_total_funds_and_numpy_statistics_equivalence() -> None:
    """Перевірка еквівалентності baseline Python loops та NumPy-векторизації."""
    balances = [1000.50, 2500.25, 3499.25, 100.0]
    assert total_funds_numpy(balances) == pytest.approx(total_funds_python(balances))

    amounts = [120.5, 450.0, 89.25, 1340.75, 500.0]
    py_stats = transaction_statistics_python(amounts)
    np_stats = transaction_statistics_numpy(amounts)

    for key in ("count", "turnover", "average", "minimum", "maximum", "std"):
        assert np_stats[key] == pytest.approx(py_stats[key], rel=1e-9, abs=1e-9)


def test_balance_from_history_and_negative_balance_guard() -> None:
    """Перевірка розрахунку балансу за великою історією та заборони від'ємного балансу."""
    history = generate_account_history(count=10_000, initial_balance=100_000.0, seed=42)
    py_res = calculate_balance_from_history_python(100_000.0, history)
    np_res = calculate_balance_from_history_numpy(100_000.0, history)

    for key in ("final_balance", "turnover", "total_inflow", "total_outflow"):
        assert np_res[key] == pytest.approx(py_res[key], rel=1e-9, abs=1e-6)

    with pytest.raises(InsufficientFundsError):
        calculate_balance_from_history_python(100.0, [50.0, -200.0])

    with pytest.raises(InsufficientFundsError):
        calculate_balance_from_history_numpy(100.0, [50.0, -200.0])


def test_parallel_statistics_threads_and_processes() -> None:
    """Перевірка коректності ThreadPoolExecutor та ProcessPoolExecutor для статистики."""
    _, _, amounts = generate_operations(count=5_000, account_count=100, seed=11)
    py_stats = transaction_statistics_python(amounts)
    thr_stats = transaction_statistics_threads(amounts, workers=2)
    proc_stats = transaction_statistics_processes(amounts, workers=2)

    for key in ("count", "turnover", "average", "minimum", "maximum", "std"):
        assert thr_stats[key] == pytest.approx(py_stats[key], rel=1e-9, abs=1e-9)
        assert proc_stats[key] == pytest.approx(py_stats[key], rel=1e-9, abs=1e-9)


def test_risk_scores_all_implementations_match() -> None:
    """Перевірка однаковості результатів Sequential, ThreadPool, ProcessPool, Process та NumPy."""
    values = [70.0, 125.5, 430.25, 999.9, 1500.0, 250.75]
    sequential = calculate_risk_scores_sequential(values, iterations=10)
    threads_res = calculate_risk_scores_threads(values, workers=2, iterations=10)
    processes_res = calculate_risk_scores_processes(
        values,
        workers=2,
        chunksize=2,
        iterations=10,
    )
    manual_proc_res = calculate_risk_scores_manual_processes(values, workers=2, iterations=10)
    numpy_res = calculate_risk_scores_numpy(values, iterations=10)

    assert threads_res == pytest.approx(sequential, rel=1e-12, abs=1e-12)
    assert processes_res == pytest.approx(sequential, rel=1e-12, abs=1e-12)
    assert manual_proc_res == pytest.approx(sequential, rel=1e-12, abs=1e-12)
    assert np.allclose(numpy_res, sequential, rtol=1e-12, atol=1e-12)


def test_io_bound_parallel_log_loading(tmp_path: Path) -> None:
    """Перевірка паралельного читання журналів операцій через ThreadPoolExecutor і Thread."""
    paths = generate_operation_log_files(
        output_dir=tmp_path,
        total_operations=1_000,
        file_count=4,
        account_count=50,
        seed=5,
    )
    seq = load_operation_logs_sequential(paths)
    pool = load_operation_logs_threadpool(paths, workers=4)
    manual, processed_count = read_logs_manual_threads(paths)

    assert pool == seq
    assert manual == seq
    assert processed_count == 4
    assert sum(len(chunk) for chunk in pool) == 1_000


def test_lock_synchronization_preserves_final_balance() -> None:
    """Перевірка незмінності фінального балансу при конкурентній роботі з Lock."""
    safe_result = run_concurrent_account_simulation(
        initial_balance=5_000.0,
        operations_per_thread=200,
        deposit_amount=50.0,
        withdrawal_amount=20.0,
        threads_count=4,
        use_lock=True,
    )
    assert safe_result["is_consistent"] is True
    assert safe_result["errors_count"] == 0
    assert safe_result["actual_operations"] == 1_600
    assert safe_result["actual_balance"] == pytest.approx(
        float(safe_result["expected_balance"])
    )

    state = SharedAccountState(initial_balance=100.0)
    with pytest.raises(InsufficientFundsError):
        state.withdraw_safe(200.0)
    with pytest.raises(InvalidAmountError):
        state.deposit_safe(0.0)


def test_caching_and_invalidation() -> None:
    """Перевірка роботи @lru_cache (hits/misses) та інвалідації після зміни даних."""
    ledger = BankAnalyticsLedger(maxsize=64)
    ledger.register_account(
        account_id=1,
        initial_balance=2_000.0,
        operations=[100.0, 200.0, 300.0],
    )

    first = ledger.get_account_statistics(1)
    info_after_first = ledger.cache_info()
    assert info_after_first.misses == 1
    assert info_after_first.hits == 0
    assert first["average"] == pytest.approx(200.0)

    second = ledger.get_account_statistics(1)
    info_after_second = ledger.cache_info()
    assert info_after_second.hits == 1
    assert second == first

    ledger.add_operation(account_id=1, operation_type="deposit", amount=600.0)
    updated = ledger.get_account_statistics(1)
    info_after_update = ledger.cache_info()
    assert info_after_update.misses == 2
    assert updated["count"] == 4.0
    assert updated["average"] == pytest.approx(300.0)
    assert updated["current_balance"] == pytest.approx(2_600.0)

    ledger.cache_clear()
    assert ledger.cache_info().currsize == 0
