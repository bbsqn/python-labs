"""Модуль пакетної обробки потоків (batch processing)."""

from collections.abc import Iterable, Iterator
from itertools import islice

from .models import AccountRecord


def batched_records(
    records: Iterable[AccountRecord],
    batch_size: int,
) -> Iterator[list[AccountRecord]]:
    """Розбиває вхідний потік на пакети заданого розміру через islice."""
    it = iter(records)
    while True:
        batch = list(islice(it, batch_size))
        if not batch:
            return
        yield batch


# Аліас для сумісності з тестами прикладу
batched_students = batched_records


def dynamic_batched(
    records: Iterable[AccountRecord],
    max_amount_per_batch: float = 10000.0,
) -> Iterator[list[AccountRecord]]:
    """Динамічне пакетування за накопиченою сумою операцій (Advanced)."""
    it = iter(records)
    current_batch: list[AccountRecord] = []
    current_sum = 0.0

    for rec in it:
        current_batch.append(rec)
        current_sum += rec.amount
        if current_sum >= max_amount_per_batch:
            yield current_batch
            current_batch = []
            current_sum = 0.0

    if current_batch:
        yield current_batch
