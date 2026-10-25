"""Модуль незмінюваних об'єктів-значень (Value Objects)."""

from dataclasses import dataclass
from functools import total_ordering


@total_ordering
@dataclass(frozen=True, slots=True)
class Money:
    """Незмінюваний об'єкт-значення грошової суми та валюти."""

    amount: float
    currency: str = "UAH"

    def __post_init__(self) -> None:
        if self.amount < 0:
            raise ValueError("Сума грошей не може бути від'ємною")
        object.__setattr__(self, "amount", round(self.amount, 2))

    def __add__(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            msg = (
                f"Неможливо додати різні валюти: "
                f"{self.currency} та {other.currency}"
            )
            raise ValueError(msg)
        return Money(round(self.amount + other.amount, 2), self.currency)

    def __sub__(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            msg = (
                f"Неможливо відняти різні валюти: "
                f"{self.currency} та {other.currency}"
            )
            raise ValueError(msg)
        if self.amount < other.amount:
            msg = (
                f"Результат віднімання не може бути від'ємним: "
                f"{self.amount} < {other.amount}"
            )
            raise ValueError(msg)
        return Money(round(self.amount - other.amount, 2), self.currency)

    def __mul__(self, factor: float) -> "Money":
        if factor < 0:
            raise ValueError("Множник не може бути від'ємним")
        return Money(round(self.amount * factor, 2), self.currency)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        return self.amount == other.amount and self.currency == other.currency

    def __lt__(self, other: "Money") -> bool:
        if self.currency != other.currency:
            msg = (
                f"Неможливо порівняти різні валюти: "
                f"{self.currency} та {other.currency}"
            )
            raise ValueError(msg)
        return self.amount < other.amount

    def __str__(self) -> str:
        return f"{self.amount:.2f} {self.currency}"

    def __repr__(self) -> str:
        return f"Money(amount={self.amount:.2f}, currency={self.currency!r})"
