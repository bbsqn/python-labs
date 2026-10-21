"""Модуль автоматизованих тестів для лабораторної роботи №2."""

import sys
from pathlib import Path

# Додаємо директорію src до sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import unittest  # noqa: E402
from collections import Counter  # noqa: E402

from data_processor.analytics import (  # noqa: E402
    OperationTracker,
    calculate_average_balance,
    calculate_average_values,
    calculate_total_funds,
    create_account_record,
    create_balance_filter,
    create_type_filter,
    export_summary,
    find_poorest_account,
    find_richest_account,
    pipeline,
    sort_by_balance,
)
from data_processor.decorators import (  # noqa: E402
    log_call,
    measure_time,
    repeat,
)
from data_processor.processors import (  # noqa: E402
    count_accounts_by_type,
    create_account_index,
    filter_by_min_balance,
    filter_by_type,
    filter_items,
    find_account_by_index,
    find_account_by_number,
    get_unique_types,
    group_accounts_by_type,
    group_by_nested,
    sort_accounts,
)


class TestProcessors(unittest.TestCase):
    """Набір тестів для перевірки функцій обробки структур даних."""

    def setUp(self) -> None:
        self.sample_accounts = [
            {
                "id": 1,
                "account_number": "UA001",
                "client_name": "Тест 1",
                "balance": 1000.0,
                "account_type": "debit",
                "currency": "UAH",
            },
            {
                "id": 2,
                "account_number": "UA002",
                "client_name": "Тест 2",
                "balance": 5000.0,
                "account_type": "savings",
                "currency": "UAH",
            },
            {
                "id": 3,
                "account_number": "UA003",
                "client_name": "Тест 3",
                "balance": 200.0,
                "account_type": "credit",
                "currency": "USD",
            },
        ]

    def test_get_unique_types(self) -> None:
        types = get_unique_types(self.sample_accounts)
        self.assertIsInstance(types, set)
        self.assertEqual(types, {"debit", "savings", "credit"})

    def test_create_account_index(self) -> None:
        index = create_account_index(self.sample_accounts)
        self.assertIsInstance(index, dict)
        self.assertIn("UA001", index)
        self.assertEqual(index["UA002"]["balance"], 5000.0)

    def test_find_account_by_number(self) -> None:
        found = find_account_by_number(self.sample_accounts, "UA002")
        self.assertIsNotNone(found)
        assert found is not None
        self.assertEqual(found["client_name"], "Тест 2")

    def test_find_account_by_number_not_found(self) -> None:
        found = find_account_by_number(self.sample_accounts, "NON_EXISTING")
        self.assertIsNone(found)

    def test_find_account_by_index(self) -> None:
        index = create_account_index(self.sample_accounts)
        found = find_account_by_index(index, "UA001")
        self.assertIsNotNone(found)
        assert found is not None
        self.assertEqual(found["client_name"], "Тест 1")

    def test_filter_by_type(self) -> None:
        filtered = filter_by_type(self.sample_accounts, "savings")
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["account_number"], "UA002")

    def test_filter_by_min_balance(self) -> None:
        filtered = filter_by_min_balance(self.sample_accounts, 1000.0)
        self.assertEqual(len(filtered), 2)

    def test_group_accounts_by_type(self) -> None:
        grouped = group_accounts_by_type(self.sample_accounts)
        self.assertIn("debit", grouped)
        self.assertEqual(len(grouped["debit"]), 1)
        self.assertIn("savings", grouped)

    def test_count_accounts_by_type(self) -> None:
        counts = count_accounts_by_type(self.sample_accounts)
        self.assertIsInstance(counts, Counter)
        self.assertEqual(counts["debit"], 1)
        self.assertEqual(counts["savings"], 1)

    def test_filter_items_higher_order(self) -> None:
        res = filter_items(
            self.sample_accounts,
            lambda a: a["balance"] > 1000.0,
        )
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["account_number"], "UA002")

    def test_sort_accounts_universal(self) -> None:
        res = sort_accounts(self.sample_accounts, reverse=True)
        self.assertEqual(res[0]["account_number"], "UA002")
        self.assertEqual(res[-1]["account_number"], "UA003")

    def test_group_by_nested(self) -> None:
        nested = group_by_nested(
            self.sample_accounts,
            "account_type",
            "currency",
        )
        self.assertIn("debit", nested)
        self.assertIn("UAH", nested["debit"])
        self.assertEqual(len(nested["debit"]["UAH"]), 1)


class TestAnalytics(unittest.TestCase):
    """Набір тестів для модуля аналітики, замикань та агрегації."""

    def setUp(self) -> None:
        self.sample = [
            {
                "account_number": "A1",
                "balance": 100.0,
                "account_type": "debit",
            },
            {
                "account_number": "A2",
                "balance": 500.0,
                "account_type": "savings",
            },
        ]

    def test_calculate_total_funds(self) -> None:
        total = calculate_total_funds(self.sample)
        self.assertEqual(total, 600.0)

    def test_calculate_average_balance(self) -> None:
        avg = calculate_average_balance(self.sample)
        self.assertEqual(avg, 300.0)

    def test_calculate_average_empty(self) -> None:
        self.assertEqual(calculate_average_balance([]), 0.0)

    def test_find_richest_and_poorest(self) -> None:
        richest = find_richest_account(self.sample)
        poorest = find_poorest_account(self.sample)
        self.assertIsNotNone(richest)
        self.assertIsNotNone(poorest)
        assert richest is not None and poorest is not None
        self.assertEqual(richest["account_number"], "A2")
        self.assertEqual(poorest["account_number"], "A1")

    def test_sort_by_balance(self) -> None:
        sorted_accs = sort_by_balance(self.sample, reverse=False)
        self.assertEqual(sorted_accs[0]["account_number"], "A1")
        self.assertEqual(sorted_accs[1]["account_number"], "A2")

    def test_calculate_average_values_args(self) -> None:
        self.assertEqual(calculate_average_values(10.0, 20.0, 30.0), 20.0)
        self.assertEqual(calculate_average_values(), 0.0)

    def test_create_account_record_kwargs(self) -> None:
        rec = create_account_record(
            account_number="A99",
            balance=999.0,
            status="active",
        )
        self.assertEqual(rec["account_number"], "A99")
        self.assertEqual(rec["balance"], 999.0)
        self.assertEqual(rec["status"], "active")

    def test_create_balance_filter_closure(self) -> None:
        filter_50 = create_balance_filter(50.0)
        filter_200 = create_balance_filter(200.0)
        self.assertTrue(filter_50(self.sample[0]))
        self.assertFalse(filter_200(self.sample[0]))

    def test_create_type_filter_closure(self) -> None:
        filter_debit = create_type_filter("debit")
        self.assertTrue(filter_debit(self.sample[0]))
        self.assertFalse(filter_debit(self.sample[1]))

    def test_operation_tracker_deque(self) -> None:
        tracker = OperationTracker(maxlen=2)
        tracker.record_operation("op1")
        tracker.record_operation("op2")
        tracker.record_operation("op3")
        recent = tracker.get_recent()
        self.assertEqual(len(recent), 2)
        self.assertEqual(recent, ["op2", "op3"])

    def test_export_summary(self) -> None:
        summary = export_summary(self.sample)
        self.assertEqual(summary["count"], 2)
        self.assertEqual(summary["total_funds"], 600.0)
        self.assertEqual(summary["average_balance"], 300.0)

    def test_pipeline_processing(self) -> None:
        result = pipeline(
            self.sample,
            lambda items: [a for a in items if a["balance"] > 200.0],
            lambda items: sort_by_balance(items, reverse=True),
        )
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["account_number"], "A2")


class TestDecorators(unittest.TestCase):
    """Набір тестів для декораторів."""

    def test_repeat_decorator(self) -> None:
        counter = 0

        @repeat(count=3)
        def increment() -> int:
            nonlocal counter
            counter += 1
            return counter

        res = increment()
        self.assertEqual(counter, 3)
        self.assertEqual(res, 3)

    def test_measure_time_decorator(self) -> None:
        @measure_time
        def compute() -> int:
            return 42

        self.assertEqual(compute(), 42)

    def test_log_call_decorator(self) -> None:
        @log_call
        def sample() -> str:
            return "ok"

        self.assertEqual(sample(), "ok")


if __name__ == "__main__":
    unittest.main()
