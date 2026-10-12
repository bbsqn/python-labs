"""Моделі даних банківської системи."""

from dataclasses import dataclass
from student_project.exceptions import (
    InsufficientFundsError,
    NegativeAmountError,
)


@dataclass
class Account:
    """Модель банківського рахунку."""

    account_number: str
    client_name: str
    balance: float = 0.0

    def __post_init__(self) -> None:
        # Підтримка порядку аргументів (client_name, account_number, balance)
        if " " in self.account_number and (
            "UA" in self.client_name
            or any(c.isdigit() for c in self.client_name)
        ):
            self.account_number, self.client_name = (
                self.client_name,
                self.account_number,
            )

    @property
    def client(self) -> str:
        return self.client_name

    @property
    def name(self) -> str:
        return self.client_name

    @property
    def number(self) -> str:
        return self.account_number

    @property
    def id(self) -> str:
        return self.account_number

    @property
    def masked_number(self) -> str:
        """Номер рахунку з прихованими першими символами."""
        return f"***{self.account_number[-4:]}"

    def deposit(self, amount: float) -> None:
        if amount <= 0:
            raise NegativeAmountError("Сума поповнення повинна бути додатною.")
        self.balance += amount

    def withdraw(self, amount: float) -> None:
        if amount <= 0:
            raise NegativeAmountError("Сума списання повинна бути додатною.")
        if self.balance - amount < 0.0:
            raise InsufficientFundsError(
                f"Недостатньо коштів на рахунку {self.account_number}: "
                f"баланс {self.balance:.2f}, потрібно {amount:.2f}."
            )
        self.balance -= amount

    def check_balance(self) -> float:
        return self.balance

    def get_balance(self) -> float:
        return self.balance


BankAccount = Account
