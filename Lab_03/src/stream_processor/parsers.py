"""Модуль генераторів синтаксичного аналізу CSV рядків."""

import csv
from collections.abc import Iterable, Iterator
from itertools import count
from typing import Any

from .models import AccountRecord


def parse_csv_rows(lines: Iterable[str]) -> Iterator[dict[str, str]]:
    """Потоковий розбір CSV рядків у словники за допомогою yield from."""
    reader = csv.DictReader(lines)
    yield from reader


def infinite_account_stream(
    start_index: int = 1,
) -> Iterator[AccountRecord]:
    """Генератор нескінченного потоку рахунків на основі itertools.count."""
    for i in count(start_index):
        yield AccountRecord(
            account_number=f"UA{i:07d}",
            client=f"Клієнт {i}",
            balance=1000.0 + (i % 100) * 50.0,
            operation="deposit",
            amount=100.0,
        )


def recursive_flatten(values: Iterable[Any]) -> Iterator[Any]:
    """Рекурсивний генератор сплощення вкладених списків із yield from."""
    for item in values:
        if isinstance(item, (list, tuple)):
            yield from recursive_flatten(item)
        else:
            yield item
