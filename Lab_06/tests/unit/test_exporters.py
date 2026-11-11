"""Модульні тести імпорту/експорту файлів з використанням фікстури tmp_path."""

import json
from pathlib import Path

import pytest

from bank_system.exceptions import DataExportError, DataImportError
from bank_system.exporters import export_accounts_json, import_accounts_csv
from bank_system.models import Account


def test_export_accounts_json_creates_valid_file(tmp_path: Path, sample_account: Account) -> None:
    """Перевірка коректного створення та структури вихідного JSON-файлу через tmp_path."""
    output_file = tmp_path / "accounts_export.json"

    export_accounts_json([sample_account], output_file)

    assert output_file.exists()
    content = json.loads(output_file.read_text(encoding="utf-8"))
    assert len(content) == 1
    record = content[0]
    assert record["account_number"] == "UA10000001"
    assert record["client"] == "Остап Зінчук"
    assert record["balance"] == pytest.approx(1500.50)
    assert record["currency"] == "UAH"


def test_import_accounts_csv_valid_file(tmp_path: Path) -> None:
    """Перевірка зчитування валідних рахунків з тимчасового CSV-файлу."""
    csv_file = tmp_path / "valid_accounts.csv"
    csv_file.write_text(
        "account_number,client,balance,currency\n"
        "UA00000001,Остап Зінчук,1200.50,UAH\n"
        "UA00000002,Марія Коваль,3500.00,USD\n",
        encoding="utf-8",
    )

    accounts = import_accounts_csv(csv_file)

    assert len(accounts) == 2
    assert accounts[0].account_number == "UA00000001"
    assert accounts[0].balance == pytest.approx(1200.50)
    assert accounts[1].currency == "USD"


def test_import_accounts_csv_non_existent_file(tmp_path: Path) -> None:
    """Перевірка винятку DataImportError при спробі імпорту неіснуючого файлу."""
    missing_file = tmp_path / "non_existent.csv"
    with pytest.raises(DataImportError, match="Файл імпорту не існує"):
        import_accounts_csv(missing_file)


def test_import_accounts_csv_missing_headers_raises(tmp_path: Path) -> None:
    """Перевірка винятку при відсутності обов'язкових колонок у CSV."""
    bad_csv = tmp_path / "bad_header.csv"
    bad_csv.write_text("random_col1,random_col2\n1,2\n", encoding="utf-8")

    with pytest.raises(DataImportError, match="не містить обов'язкових колонок"):
        import_accounts_csv(bad_csv)


def test_import_accounts_csv_malformed_balance_raises(tmp_path: Path) -> None:
    """Перевірка виявлення некоректного числового значення балансу в рядку CSV."""
    malformed_csv = tmp_path / "malformed.csv"
    malformed_csv.write_text(
        "account_number,client,balance,currency\n"
        "UA00000001,Тестовий Клієнт,not_a_number,UAH\n",
        encoding="utf-8",
    )

    with pytest.raises(DataImportError, match="некоректне значення балансу"):
        import_accounts_csv(malformed_csv)


def test_import_accounts_csv_empty_fields_raises(tmp_path: Path) -> None:
    """Перевірка виявлення порожніх обов'язкових полів у рядку CSV."""
    empty_csv = tmp_path / "empty_fields.csv"
    empty_csv.write_text(
        "account_number,client,balance,currency\n"
        ",,500.0,UAH\n",
        encoding="utf-8",
    )

    with pytest.raises(DataImportError, match="порожні обов'язкові поля"):
        import_accounts_csv(empty_csv)


def test_export_accounts_json_os_error_raises(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Перевірка обробки системної помилки збереження файлу в export_accounts_json."""
    from pathlib import Path as RealPath

    def broken_write_text(*args: object, **kwargs: object) -> None:
        raise OSError("Диск захищено від запису")

    monkeypatch.setattr(RealPath, "write_text", broken_write_text)
    out_file = tmp_path / "error.json"

    with pytest.raises(DataExportError, match="Помилка експорту в JSON"):
        export_accounts_json([], out_file)
