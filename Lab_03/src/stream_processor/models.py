"""Модуль моделей даних та власних класів-ітераторів."""

from collections.abc import Iterator
from typing import NamedTuple


class AccountRecord(NamedTuple):
    """Незмінюваний запис банківського рахунку та операції."""

    account_number: str
    client: str
    balance: float
    operation: str
    amount: float

    @property
    def id(self) -> str:
        """Аліас для сумісності з generic кодом."""
        return self.account_number

    @property
    def name(self) -> str:
        """Аліас імені клієнта."""
        return self.client

    @property
    def grade(self) -> float:
        """Аліас числового показника."""
        return self.balance


# Аліас для сумісності з прикладом методички
StudentRecord = AccountRecord


class AccountRangeIterator(Iterator[int]):
    """Власний ітератор діапазону чисел/індексів (Section 6)."""

    def __init__(self, start: int, stop: int, step: int = 1) -> None:
        self.current = start
        self.stop = stop
        self.step = step

    def __iter__(self) -> "AccountRangeIterator":
        return self

    def __next__(self) -> int:
        if self.current >= self.stop:
            raise StopIteration
        value = self.current
        self.current += self.step
        return value


class AccountRange:
    """Клас iterable, що розділяє контейнер та ітератор (Section 7)."""

    def __init__(self, start: int, stop: int, step: int = 1) -> None:
        self.start = start
        self.stop = stop
        self.step = step

    def __iter__(self) -> AccountRangeIterator:
        return AccountRangeIterator(self.start, self.stop, self.step)
