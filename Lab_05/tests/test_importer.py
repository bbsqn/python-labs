"""Модульні тести для надійного модуля імпорту та експорту (Lab 5)."""

# flake8: noqa: E402
from pathlib import Path
import sys
import unittest

SRC_DIR = str(Path(__file__).resolve().parent.parent / "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from reliable_importer.config import load_config, validate_config
from reliable_importer.exceptions import (
    ApplicationError,
    ConfigurationError,
    DataExportError,
    DataImportError,
    RecordValidationError,
)
from reliable_importer.exporters import export_accounts_json
from reliable_importer.logging_config import mask_sensitive_account
from reliable_importer.models import (
    AppConfig,
    BankAccountRecord,
    LoggingConfig,
    ProcessingConfig,
)
from reliable_importer.readers import read_csv_rows
from reliable_importer.services import (
    ImportStatistics,
    filter_by_balance,
    import_accounts,
)
from reliable_importer.utils import logged_operation
from reliable_importer.validators import parse_account


class TestReliableImporter(unittest.TestCase):
    """Набір модульних тестів для перевірки надійності та коректності."""

    def setUp(self) -> None:
        self.test_dir = Path(__file__).resolve().parent / "test_sandbox"
        self.test_dir.mkdir(parents=True, exist_ok=True)
        self.sample_csv = self.test_dir / "sample.csv"
        self.sample_csv.write_text(
            "account_number,client,balance,operation,amount\n"
            "UA01,Іван Петренко,1000.00,deposit,200.00\n"
            "UA02,Олена Коваль,500.00,withdraw,100.00\n"
            "UA03,Василь Бойко,100.00,withdraw,500.00\n"
            "UA04,,300.00,deposit,50.00\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        if self.test_dir.exists():
            for f in self.test_dir.glob("*"):
                try:
                    f.unlink()
                except OSError:
                    pass
            try:
                self.test_dir.rmdir()
            except OSError:
                pass

    def test_exception_hierarchy(self) -> None:
        err = RecordValidationError("Bad record", line_number=5, field="client")
        self.assertIsInstance(err, ApplicationError)
        self.assertEqual(err.line_number, 5)
        self.assertEqual(err.field, "client")

    def test_validators(self) -> None:
        # Валідний депозит
        row_deposit = {
            "account_number": "UA01",
            "client": "Іван",
            "balance": "1000.0",
            "operation": "deposit",
            "amount": "200.0",
        }
        acc = parse_account(row_deposit, line_number=2)
        self.assertEqual(acc.new_balance, 1200.0)

        # Валідне зняття
        row_withdraw = {
            "account_number": "UA01",
            "client": "Іван",
            "balance": "1000.0",
            "operation": "withdraw",
            "amount": "200.0",
        }
        acc2 = parse_account(row_withdraw, line_number=3)
        self.assertEqual(acc2.new_balance, 800.0)

        # Зняття більше балансу (недопущення овердрафту)
        row_overdraft = {
            "account_number": "UA01",
            "client": "Іван",
            "balance": "100.0",
            "operation": "withdraw",
            "amount": "500.0",
        }
        with self.assertRaises(RecordValidationError):
            parse_account(row_overdraft, line_number=4)

        # Невалідне число балансу (Exception Chaining)
        row_invalid_num = {
            "account_number": "UA01",
            "client": "Іван",
            "balance": "abc",
            "operation": "deposit",
            "amount": "50.0",
        }
        with self.assertRaises(RecordValidationError) as ctx:
            parse_account(row_invalid_num, line_number=5)
        self.assertIsInstance(ctx.exception.__cause__, ValueError)

    def test_mask_sensitive_account(self) -> None:
        masked = mask_sensitive_account("UA1234567890")
        self.assertEqual(masked, "UA12****7890")

    def test_readers_and_file_errors(self) -> None:
        rows = list(read_csv_rows(self.sample_csv))
        self.assertEqual(len(rows), 4)
        self.assertEqual(rows[0][0], 2)  # Перший рядок даних має line_number=2

        non_existing = self.test_dir / "non_existing.csv"
        with self.assertRaises(DataImportError):
            list(read_csv_rows(non_existing))

    def test_strict_vs_tolerant_import(self) -> None:
        stats = ImportStatistics()

        # Tolerant mode (пропускає 2 некоректні записи)
        recs = list(
            import_accounts(
                self.sample_csv,
                skip_invalid=True,
                statistics=stats,
            )
        )
        self.assertEqual(len(recs), 2)
        self.assertEqual(stats.valid, 2)
        self.assertEqual(stats.invalid, 2)

        # Strict mode (падає на першому некоректному записі UA03)
        stats_strict = ImportStatistics()
        with self.assertRaises(RecordValidationError):
            list(
                import_accounts(
                    self.sample_csv,
                    skip_invalid=False,
                    statistics=stats_strict,
                )
            )

    def test_atomic_export(self) -> None:
        out_json = self.test_dir / "output.json"
        accounts = [
            BankAccountRecord(
                "UA01", "Client 1", 100.0, "deposit", 50.0, 150.0
            ),
            BankAccountRecord(
                "UA02", "Client 2", 200.0, "withdraw", 50.0, 150.0
            ),
        ]
        count = export_accounts_json(accounts, out_json)
        self.assertEqual(count, 2)
        self.assertTrue(out_json.exists())
        self.assertFalse(out_json.with_suffix(".json.tmp").exists())

    def test_config_loader_and_validation(self) -> None:
        cfg_file = self.test_dir / "test_config.yaml"
        cfg_file.write_text(
            f"input:\n  path: {self.sample_csv}\n"
            "output:\n  path: output.json\n"
            "processing:\n  minimum_balance: 50.0\n  skip_invalid: true\n"
            "logging:\n  level: INFO\n  path: app.log\n",
            encoding="utf-8",
        )
        cfg = load_config(cfg_file)
        self.assertEqual(cfg.processing.minimum_balance, 50.0)

        # Неіснуючий вхідний файл
        invalid_cfg = AppConfig(
            input_path=Path("missing_file.csv"),
            output_path=Path("out.json"),
            processing=ProcessingConfig(0.0, True),
            logging=LoggingConfig("INFO", Path("app.log")),
        )
        with self.assertRaises(ConfigurationError):
            validate_config(invalid_cfg)

    def test_logged_operation(self) -> None:
        with logged_operation("Test op"):
            pass


if __name__ == "__main__":
    unittest.main()
