"""Модульні тести експорту даних, атомарного запису та утиліт."""

from collections.abc import Iterator
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from reliable_importer.exceptions import DataExportError
from reliable_importer.exporters import (
    atomic_write,
    export_accounts_json,
)
from reliable_importer.logging_config import mask_sensitive_account
from reliable_importer.models import BankAccountRecord
from reliable_importer.utils import logged_operation


def test_export_accounts_json_success(
    sample_records_list: list[BankAccountRecord],
    tmp_path: Path,
) -> None:
    """Перевірка успішного експорту записів у формат JSON."""
    out_file = tmp_path / "exported_accounts.json"
    exported_count = export_accounts_json(sample_records_list, out_file)

    assert exported_count == 2
    assert out_file.exists()

    with out_file.open("r", encoding="utf-8") as file:
        data = json.load(file)

    assert len(data) == 2
    assert data[0]["account_number"] == "UA10000001"
    assert data[0]["balance"] == pytest.approx(1500.50)
    assert data[1]["account_number"] == "UA10000002"


def test_export_accounts_json_atomic_cleanup_on_failure(
    sample_records_list: list[BankAccountRecord],
    tmp_path: Path,
) -> None:
    """У разі аварії серіалізації тимчасовий .tmp файл видаляється."""
    out_file = tmp_path / "broken_export.json"

    with patch(
        "json.dump",
        side_effect=OSError("Симульований збій запису на диск"),
    ):
        with pytest.raises(DataExportError) as exc_info:
            export_accounts_json(sample_records_list, out_file)

    assert "Аварія атомарного збереження" in str(exc_info.value)
    assert not out_file.exists()

    temp_files = list(tmp_path.glob("*.tmp"))
    assert len(temp_files) == 0


def test_export_accounts_json_iterator_failure(
    sample_records_list: list[BankAccountRecord],
    tmp_path: Path,
) -> None:
    """Збій ітератора перед записом викликає DataExportError."""
    out_file = tmp_path / "broken_iter.json"

    def faulty_records_generator() -> Iterator[BankAccountRecord]:
        yield sample_records_list[0]
        raise RuntimeError("Симульований збій під час генерації")

    with pytest.raises(DataExportError) as exc_info:
        export_accounts_json(
            faulty_records_generator(),
            out_file,
        )

    assert "Помилка серіалізації або запису" in str(exc_info.value)
    assert not out_file.exists()


def test_atomic_write_success(tmp_path: Path) -> None:
    """Перевірка успішного створення файлу через контекстний менеджер."""
    target = tmp_path / "atomic_target.txt"
    with atomic_write(target) as temp_target:
        assert temp_target.suffix.endswith(".tmp")
        temp_target.write_text("Дані для перевірки", encoding="utf-8")

    assert target.exists()
    assert target.read_text(encoding="utf-8") == "Дані для перевірки"


@pytest.mark.parametrize(
    ("raw_account", "expected_masked"),
    [
        ("UA10000001", "UA10****0001"),
        ("UA123456", "UA12****3456"),
        ("UA1234", "UA***34"),
        ("UA1", "U***"),
        ("", "***"),
        ("   ", "***"),
    ],
)
def test_mask_sensitive_account(
    raw_account: str,
    expected_masked: str,
) -> None:
    """Перевірка коректного маскування номерів рахунків різної довжини."""
    assert mask_sensitive_account(raw_account) == expected_masked


def test_logged_operation_success() -> None:
    """Перевірка нормального проходження контекстного менеджера утиліти."""
    executed = False
    with logged_operation("Тестова операція"):
        executed = True
    assert executed is True


def test_logged_operation_failure() -> None:
    """Контекстний менеджер реєструє помилку та коректно її прокидає."""
    with pytest.raises(ValueError, match="Збій операції"):
        with logged_operation("Невдала операція"):
            raise ValueError("Збій операції")
