"""Модуль побудови та оркестрації потокового конвеєра (pipeline)."""

import csv
from collections.abc import Iterator
from pathlib import Path

from .filters import filter_by_balance, validate_accounts
from .models import AccountRecord
from .parsers import parse_csv_rows
from .readers import clean_lines, read_lines
from .transformations import apply_operations, normalize_clients


def build_pipeline(
    path: Path,
    minimum_balance: float = 0.0,
) -> Iterator[AccountRecord]:
    """Формує лінивий потік обробки:

    read_lines -> clean_lines -> parse_csv_rows ->
    validate_accounts -> apply_operations ->
    normalize_clients -> filter_by_balance
    """
    raw_lines = read_lines(path)
    cleaned = clean_lines(raw_lines)
    parsed_rows = parse_csv_rows(cleaned)
    validated = validate_accounts(parsed_rows)
    operated = apply_operations(validated)
    normalized = normalize_clients(operated)
    filtered = filter_by_balance(normalized, minimum_balance)
    return filtered


def read_all_accounts_eager(path: Path) -> list[dict[str, str]]:
    """Eager матеріалізація всього CSV файлу в оперативну пам'ять (list)."""
    with path.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        return list(reader)


def read_accounts_lazy(path: Path) -> Iterator[dict[str, str]]:
    """Lazy потокове читання CSV рядків через yield from."""
    with path.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        yield from reader
