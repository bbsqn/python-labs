"""Потокове читання CSV файлів банківських операцій."""

from collections.abc import Iterator
import csv
from pathlib import Path

from .exceptions import DataImportError


def read_csv_rows(path: Path) -> Iterator[tuple[int, dict[str, str]]]:
    """Потокове зчитування рядків CSV файлу з нумерацією.

    Використовує генератор для економії оперативної пам'яті O(1).
    """
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)
            if reader.fieldnames is None:
                raise DataImportError(
                    f"CSV файл {path} порожній або пошкоджений."
                )

            for line_number, row in enumerate(reader, start=2):
                cleaned_row = {
                    (k.strip() if k else ""): (v.strip() if v else "")
                    for k, v in row.items()
                    if k is not None
                }
                yield line_number, cleaned_row
    except (OSError, UnicodeDecodeError) as error:
        raise DataImportError(
            f"Не вдалося прочитати CSV файл {path}: {error}"
        ) from error
