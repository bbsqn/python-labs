"""Інтеграційні тести фільтрації та атомарного збереження результатів."""

import json
from pathlib import Path

import pytest

from reliable_importer.exporters import export_accounts_json
from reliable_importer.models import BankAccountRecord
from reliable_importer.services import filter_by_balance


def test_export_pipeline_end_to_end(
    sample_records_list: list[BankAccountRecord],
    tmp_path: Path,
) -> None:
    """Інтеграція фільтрації за балансом та експорту у файл JSON."""
    out_file = tmp_path / "filtered_accounts.json"
    filtered = filter_by_balance(sample_records_list, minimum_balance=2000.0)

    count = export_accounts_json(filtered, out_file)
    assert count == 1
    assert out_file.exists()

    with out_file.open("r", encoding="utf-8") as file:
        data = json.load(file)

    assert len(data) == 1
    assert data[0]["account_number"] == "UA10000002"
    assert data[0]["balance"] == pytest.approx(3200.00)


def test_export_pipeline_empty_records(
    sample_records_list: list[BankAccountRecord],
    tmp_path: Path,
) -> None:
    """Фільтрація без збігів формує валідний порожній JSON масив."""
    out_file = tmp_path / "empty_filtered.json"
    filtered = filter_by_balance(sample_records_list, minimum_balance=50000.0)

    count = export_accounts_json(filtered, out_file)
    assert count == 0
    assert out_file.exists()

    with out_file.open("r", encoding="utf-8") as file:
        data = json.load(file)

    assert data == []


def test_export_pipeline_nested_directory_creation(
    sample_records_list: list[BankAccountRecord],
    tmp_path: Path,
) -> None:
    """Автоматичне створення вкладених каталогів для вихідного файлу."""
    nested_out = tmp_path / "nested" / "archive" / "reports" / "export.json"
    assert not nested_out.parent.exists()

    count = export_accounts_json(sample_records_list, nested_out)
    assert count == 2
    assert nested_out.exists()
