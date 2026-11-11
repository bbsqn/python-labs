"""Інтеграційні тести файлового конвеєра: імпорт CSV -> обробка -> експорт JSON."""

import json
from pathlib import Path

import pytest

from bank_system.exporters import export_accounts_json, import_accounts_csv


@pytest.mark.integration
def test_csv_to_json_full_pipeline(tmp_path: Path) -> None:
    """Інтеграційний тест: зчитування CSV, виконання бізнес-операцій та експорт у JSON."""
    csv_file = tmp_path / "incoming_accounts.csv"
    csv_file.write_text(
        "account_number,client,balance,currency\n"
        "UA00000001,Остап Зінчук,1000.00,UAH\n"
        "UA00000002,Марія Коваль,2000.00,UAH\n"
        "UA00000003,Іван Франко,3000.00,UAH\n",
        encoding="utf-8",
    )

    # 1. Імпорт даних
    accounts = import_accounts_csv(csv_file)
    assert len(accounts) == 3

    # 2. Виконання бізнес-логіки
    accounts[0].deposit(500.0)
    accounts[1].withdraw(200.0)

    # 3. Експорт у JSON
    json_output = tmp_path / "processed_accounts.json"
    export_accounts_json(accounts, json_output)

    assert json_output.exists()
    exported_data = json.loads(json_output.read_text(encoding="utf-8"))
    assert len(exported_data) == 3

    assert exported_data[0]["account_number"] == "UA00000001"
    assert exported_data[0]["balance"] == pytest.approx(1500.0)
    assert exported_data[1]["account_number"] == "UA00000002"
    assert exported_data[1]["balance"] == pytest.approx(1800.0)
    assert exported_data[2]["account_number"] == "UA00000003"
    assert exported_data[2]["balance"] == pytest.approx(3000.0)


@pytest.mark.integration
def test_empty_csv_import_and_export(tmp_path: Path) -> None:
    """Інтеграційний тест: коректна робота з порожнім списком (лише заголовки)."""
    empty_csv = tmp_path / "empty_valid.csv"
    empty_csv.write_text("account_number,client,balance,currency\n", encoding="utf-8")

    accounts = import_accounts_csv(empty_csv)
    assert len(accounts) == 0

    json_output = tmp_path / "empty_out.json"
    export_accounts_json(accounts, json_output)

    assert json_output.exists()
    content = json.loads(json_output.read_text(encoding="utf-8"))
    assert content == []
