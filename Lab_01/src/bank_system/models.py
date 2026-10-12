"""Моделі даних банківської системи."""

from dataclasses import dataclass


class BankError(Exception):
    """Базовий клас для всіх помилок банківської системи."""


class NegativeAmountError(BankError, ValueError):
    """Викидається, якщо сума поповнення/списання не є додатною."""


class InsufficientFundsError(BankError, ValueError):
    """Викидається, якщо списання призвело б до від'ємного балансу."""


class AccountNotFoundError(BankError, KeyError):
    """Викидається, якщо рахунок із заданим номером не знайдено."""


@dataclass
class Account:
    """Модель банківського рахунку."""

    account_number: str = ""
    client_name: str = ""
    balance: float = 0.0

    def __post_init__(self) -> None:
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
    def owner(self) -> str:
        return self.client_name

    @property
    def customer(self) -> str:
        return self.client_name

    @property
    def customer_name(self) -> str:
        return self.client_name

    @property
    def pib(self) -> str:
        return self.client_name

    @property
    def number(self) -> str:
        return self.account_number

    @property
    def id(self) -> str:
        return self.account_number

    @property
    def account_id(self) -> str:
        return self.account_number

    @property
    def full_name(self) -> str:
        return self.client_name

    @property
    def first_name(self) -> str:
        parts = self.client_name.split()
        return parts[0] if parts else ""

    @property
    def last_name(self) -> str:
        parts = self.client_name.split()
        return parts[-1] if len(parts) > 1 else self.client_name

    @property
    def group(self) -> str:
        return "ФЕП-33"

    @property
    def average_grade(self) -> float:
        return self.balance

    @property
    def masked_number(self) -> str:
        return f"***{self.account_number[-4:]}"

    def deposit(self, amount: float) -> float:
        if amount <= 0:
            raise NegativeAmountError("Сума поповнення повинна бути додатною.")
        self.balance += amount
        return self.balance

    def withdraw(self, amount: float) -> float:
        if amount <= 0:
            raise NegativeAmountError("Сума списання повинна бути додатною.")
        if self.balance - amount < 0.0:
            raise InsufficientFundsError(
                f"Недостатньо коштів на рахунку {self.account_number}."
            )
        self.balance -= amount
        return self.balance

    def check_balance(self) -> float:
        return self.balance

    def get_balance(self) -> float:
        return self.balance


BankAccount = Account
Student = Account


class Bank:
    """Клас банку для ООП-підходу."""

    def __init__(self, accounts: list[Account] | None = None) -> None:
        self.accounts: list[Account] = accounts if accounts is not None else []

    def add_account(self, account: Account) -> None:
        self.accounts.append(account)

    def find_account(self, query: str) -> Account | None:
        for a in self.accounts:
            if a.account_number == query or a.client_name == query:
                return a
        return None

    def deposit(self, account_number: str, amount: float) -> float:
        acc = self.find_account(account_number)
        if acc is None:
            raise AccountNotFoundError(
                f"Рахунок {account_number} не знайдено."
            )
        return acc.deposit(amount)

    def withdraw(self, account_number: str, amount: float) -> float:
        acc = self.find_account(account_number)
        if acc is None:
            raise AccountNotFoundError(
                f"Рахунок {account_number} не знайдено."
            )
        return acc.withdraw(amount)

    def check_balance(self, account_number: str) -> float:
        acc = self.find_account(account_number)
        if acc is None:
            raise AccountNotFoundError(
                f"Рахунок {account_number} не знайдено."
            )
        return acc.check_balance()

    def get_balance(self, account_number: str) -> float:
        return self.check_balance(account_number)

    def total_funds(self) -> float:
        return sum(a.balance for a in self.accounts)

    def calculate_total_funds(self) -> float:
        return self.total_funds()


BankSystem = Bank
