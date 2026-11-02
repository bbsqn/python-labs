"""Інтеграційні тести конвеєра зчитування та валідації CSV файлів."""

from pathlib import Path

import pytest

from reliable_importer.exceptions import DataImportError, RecordValidationError
from reliable_importer.services import ImportStatistics, import_accounts


def test_import_pipeline_valid_file(sample_csv_file: Path) -> None:
    """Повний цикл зчитування та валідації валідного CSV файлу з диска."""
    stats = ImportStatistics()
    records = list(
        import_accounts(
            sample_csv_file,
            skip_invalid=False,
            statistics=stats,
        )
    )

    assert len(records) == 3
    assert stats.total == 3
    assert stats.valid == 3
    assert stats.invalid == 0

    assert records[0].account_number == "UA10000001"
    assert records[0].client == "Остап Зінчук"
    assert records[0].balance == pytest.approx(1500.50)
    assert records[0].new_balance == pytest.approx(1700.50)

    assert records[1].account_number == "UA10000002"
    assert records[1].new_balance == pytest.approx(2700.00)


def test_import_pipeline_tolerant_filtering(
    malformed_csv_file: Path,
) -> None:
    """Інтеграція толерантного режиму: фільтрація некоректних рядків."""
    stats = ImportStatistics()
    records = list(
        import_accounts(
            malformed_csv_file,
            skip_invalid=True,
            statistics=stats,
        )
    )

    assert len(records) == 2
    assert stats.total == 4
    assert stats.valid == 2
    assert stats.invalid == 2
    assert [r.account_number for r in records] == [
        "UA10000001",
        "UA10000003",
    ]


def test_import_pipeline_empty_file_error(tmp_path: Path) -> None:
    """Спроба імпорту порожнього CSV файлу генерує DataImportError."""
    empty_csv = tmp_path / "empty.csv"
    empty_csv.write_text("", encoding="utf-8")

    stats = ImportStatistics()
    with pytest.raises(DataImportError) as exc_info:
        list(
            import_accounts(
                empty_csv,
                skip_invalid=True,
                statistics=stats,
            )
        )

    assert "порожній або пошкоджений" in str(exc_info.value)


def test_import_pipeline_strict_stops_at_first_error(
    malformed_csv_file: Path,
) -> None:
    """У строгому режимі зчитування припиняється на некоректному рядку."""
    stats = ImportStatistics()
    with pytest.raises(RecordValidationError):
        list(
            import_accounts(
                malformed_csv_file,
                skip_invalid=False,
                statistics=stats,
            )
        )

    assert stats.invalid == 1
    assert stats.total == 2
