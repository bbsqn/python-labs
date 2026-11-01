"""Модуль потокового зчитування зовнішніх CSV та JSONL файлів."""

from collections.abc import Iterator
import csv
import json
from pathlib import Path

from .exceptions import DataImportError


def read_csv_rows(path: Path) -> Iterator[tuple[int, dict[str, str]]]:
    """Потоково повертає кортеж (номер рядка, словник) із CSV-файлу."""
    try:
        with path.open("r", encoding="utf-8", newline="") as file:
            reader = csv.DictReader(file)
            for line_number, row in enumerate(reader, start=2):
                yield line_number, row
    except OSError as error:
        raise DataImportError(
            f"Помилка читання вхідного файлу: {path}"
        ) from error


def read_jsonl_rows(path: Path) -> Iterator[tuple[int, dict[str, object]]]:
    """Потоково повертає (номер рядка, об'єкт) із JSON Lines файлу."""
    try:
        with path.open("r", encoding="utf-8") as file:
            for line_number, line in enumerate(file, start=1):
                clean_line = line.strip()
                if not clean_line:
                    continue
                try:
                    data = json.loads(clean_line)
                    if isinstance(data, dict):
                        yield line_number, data
                except json.JSONDecodeError as error:
                    raise DataImportError(
                        f"Некоректний JSON рядок #{line_number}"
                    ) from error
    except OSError as error:
        raise DataImportError(
            f"Помилка читання JSONL файлу: {path}"
        ) from error
