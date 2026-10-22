"""Модульні тести для потокового конвеєра обробки банківських рахунків."""

# flake8: noqa: E402

from itertools import islice
from pathlib import Path
import sys
import unittest

# Додаємо src до sys.path для запуску тестів без встановлення пакету
SRC_DIR = str(Path(__file__).resolve().parent.parent / "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from stream_processor.analytics import (
    calculate_statistics,
    cumulative_balances,
    group_by_operation,
    pairwise_amount_differences,
    streaming_average_balance,
    streaming_total_funds,
)
from stream_processor.batches import batched_records, dynamic_batched
from stream_processor.filters import (
    filter_by_balance,
    filter_by_client,
    find_first_account,
    validate_accounts,
)
from stream_processor.models import AccountRange, AccountRecord
from stream_processor.parsers import (
    infinite_account_stream,
    parse_csv_rows,
    recursive_flatten,
)
from stream_processor.pipeline import (
    build_pipeline,
    read_accounts_lazy,
    read_all_accounts_eager,
)
from stream_processor.readers import (
    clean_lines,
    read_files_chain,
    read_lines,
)
from stream_processor.transformations import (
    apply_operations,
    normalize_clients,
)


class TestStreamProcessor(unittest.TestCase):
    """Набір тестів для перевірки коректності всіх компонентів Lab 3."""

    def setUp(self) -> None:
        self.sample_csv_text = (
            "account_number,client,balance,operation,amount\n"
            "UA0000001,  ivan petrenko ,1500.50,deposit,200.00\n"
            "UA0000002,olena koval,500.00,withdraw,100.00\n"
            "UA0000003,vasyl boyko,300.00,withdraw,600.00\n"
            "UA0000004,anna melnyk,2500.00,check,0.00\n"
            "INVALID_1,,500.00,deposit,100.00\n"
            "UA0000005,taras shevchenko,invalid,deposit,100.00\n"
            "UA0000006,lesya ukrainka,-50.00,deposit,100.00\n"
            "UA0000007,ivan franko,1200.00,invalid_op,100.00\n"
        )
        self.test_dir = Path(__file__).resolve().parent / "test_data"
        self.test_dir.mkdir(exist_ok=True)
        self.test_file = self.test_dir / "temp_accounts.csv"
        self.test_file.write_text(self.sample_csv_text, encoding="utf-8")

    def tearDown(self) -> None:
        if self.test_file.exists():
            self.test_file.unlink()
        if self.test_dir.exists():
            self.test_dir.rmdir()

    def test_models_and_custom_iterator(self) -> None:
        acc = AccountRecord("UA01", "Client", 100.0, "deposit", 50.0)
        self.assertEqual(acc.id, "UA01")
        self.assertEqual(acc.name, "Client")
        self.assertEqual(acc.grade, 100.0)

        # Перевірка багаторазової ітерованості AccountRange
        ar = AccountRange(1, 4)
        self.assertEqual(list(ar), [1, 2, 3])
        self.assertEqual(list(ar), [1, 2, 3])

    def test_readers(self) -> None:
        lines = list(read_lines(self.test_file))
        self.assertEqual(len(lines), 9)

        cleaned = list(clean_lines(["  hello  \n", "   \n", "world\n"]))
        self.assertEqual(cleaned, ["hello", "world"])

        chained = list(read_files_chain(self.test_file, self.test_file))
        self.assertEqual(len(chained), 18)

    def test_parsers(self) -> None:
        lines = [
            "account_number,client,balance,operation,amount",
            "UA01,Test Client,100,deposit,20",
        ]
        parsed = list(parse_csv_rows(lines))
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0]["account_number"], "UA01")

        # Recursive flatten
        nested = [1, [2, [3, 4], 5], 6]
        self.assertEqual(list(recursive_flatten(nested)), [1, 2, 3, 4, 5, 6])

        # Infinite stream + islice
        inf = infinite_account_stream(10)
        three = list(islice(inf, 3))
        self.assertEqual(len(three), 3)
        self.assertEqual(three[0].account_number, "UA0000010")

    def test_filters_and_validation(self) -> None:
        raw_rows = [
            {
                "account_number": "UA01",
                "client": "Ivan",
                "balance": "100",
                "operation": "deposit",
                "amount": "10",
            },
            {
                "account_number": "",
                "client": "Ivan",
                "balance": "100",
                "operation": "deposit",
                "amount": "10",
            },
            {
                "account_number": "UA02",
                "client": "Oleh",
                "balance": "-5",
                "operation": "deposit",
                "amount": "10",
            },
            {
                "account_number": "UA03",
                "client": "Anna",
                "balance": "100",
                "operation": "unknown",
                "amount": "10",
            },
        ]
        valid = list(validate_accounts(raw_rows))
        self.assertEqual(len(valid), 1)
        self.assertEqual(valid[0].account_number, "UA01")

        filtered_bal = list(filter_by_balance(valid, 150))
        self.assertEqual(len(filtered_bal), 0)

        filtered_client = list(filter_by_client(valid, "iva"))
        self.assertEqual(len(filtered_client), 1)

        # Early termination
        found = find_first_account(valid, lambda a: a.client == "Ivan")
        self.assertIsNotNone(found)
        if found:
            self.assertEqual(found.account_number, "UA01")

    def test_transformations(self) -> None:
        recs = [
            AccountRecord("UA01", "  ivan koval  ", 100.0, "deposit", 50.0),
            AccountRecord("UA02", "olena boyko", 100.0, "withdraw", 40.0),
            # insufficient funds:
            AccountRecord("UA03", "vasyl melnyk", 100.0, "withdraw", 150.0),
            AccountRecord("UA04", "taras shevchenko", 100.0, "check", 0.0),
        ]
        normalized = list(normalize_clients(recs))
        self.assertEqual(normalized[0].client, "Ivan Koval")

        operated = list(apply_operations(recs))
        self.assertEqual(operated[0].balance, 150.0)  # 100 + 50
        self.assertEqual(operated[1].balance, 60.0)   # 100 - 40
        self.assertEqual(operated[2].balance, 100.0)  # rejected, stays 100
        self.assertEqual(operated[3].balance, 100.0)  # check, unchanged

    def test_batches(self) -> None:
        recs = [
            AccountRecord(f"UA{i}", f"C{i}", 100.0, "deposit", 20.0)
            for i in range(5)
        ]
        batches = list(batched_records(recs, 2))
        self.assertEqual(len(batches), 3)
        self.assertEqual(len(batches[0]), 2)
        self.assertEqual(len(batches[1]), 2)
        self.assertEqual(len(batches[2]), 1)

        dyn_batches = list(dynamic_batched(recs, max_amount_per_batch=35.0))
        self.assertEqual(len(dyn_batches), 3)

    def test_analytics(self) -> None:
        recs = [
            AccountRecord("UA01", "C1", 100.0, "deposit", 10.0),
            AccountRecord("UA02", "C2", 200.0, "withdraw", 20.0),
            AccountRecord("UA03", "C3", 300.0, "deposit", 30.0),
        ]
        stats = calculate_statistics(recs)
        self.assertEqual(stats["count"], 3)
        self.assertEqual(stats["total"], 600.0)
        self.assertEqual(stats["average"], 200.0)
        self.assertEqual(stats["minimum"], 100.0)
        self.assertEqual(stats["maximum"], 300.0)
        self.assertEqual(stats["operations"]["deposit"], 2)

        self.assertEqual(streaming_total_funds(recs), 600.0)
        self.assertEqual(streaming_average_balance(recs), 200.0)

        cum = list(cumulative_balances(recs))
        self.assertEqual(cum, [100.0, 300.0, 600.0])

        diffs = list(pairwise_amount_differences(recs))
        self.assertEqual(diffs, [10.0, 10.0])

        grouped = list(group_by_operation(recs))
        self.assertEqual(len(grouped), 2)

    def test_pipeline_integration(self) -> None:
        pipe = build_pipeline(self.test_file, minimum_balance=400.0)
        results = list(pipe)
        # UA0000001: 1500.50 + 200.00 = 1700.50 (valid)
        # UA0000002: 500.00 - 100.00 = 400.00 (valid, >= 400)
        # UA0000003: 300 - 600 -> rejected, stays 300 (< 400, filtered out)
        # UA0000004: 2500.00 check -> 2500.00 (valid)
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0].balance, 1700.50)
        self.assertEqual(results[0].client, "Ivan Petrenko")
        self.assertEqual(results[1].balance, 400.00)
        self.assertEqual(results[2].balance, 2500.00)

        # Eager vs Lazy readers
        eager_rows = read_all_accounts_eager(self.test_file)
        self.assertEqual(len(eager_rows), 8)

        lazy_rows = list(read_accounts_lazy(self.test_file))
        self.assertEqual(len(lazy_rows), 8)


if __name__ == "__main__":
    unittest.main()
