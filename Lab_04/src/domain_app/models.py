"""Модуль доменних сутностей та ієрархії банківських рахунків."""

from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import datetime

from .value_objects import Money


class FeePolicy(ABC):
    """Абстрактна стратегія розрахунку комісії за операцію."""

    @abstractmethod
    def calculate_fee(self, amount: Money) -> Money:
        """Обчислює суму комісії."""
        ...


class ZeroFeePolicy(FeePolicy):
    """Політика нульової комісії."""

    def calculate_fee(self, amount: Money) -> Money:
        return Money(0.0, amount.currency)


class PercentageFeePolicy(FeePolicy):
    """Політика процентної комісії."""

    def __init__(self, percent: float) -> None:
        if not (0.0 <= percent <= 100.0):
            raise ValueError("Відсоток комісії повинен бути від 0 до 100")
        self._percent = percent

    @property
    def percent(self) -> float:
        return self._percent

    def calculate_fee(self, amount: Money) -> Money:
        return amount * (self._percent / 100.0)


@dataclass
class Customer:
    """Доменна сутність банківського клієнта."""

    id: int
    name: str
    email: str
    phone: str | None = None

    @property
    def display_name(self) -> str:
        return f"{self.name} <{self.email}>"


@dataclass(frozen=True, slots=True)
class Transaction:
    """Незмінюваний запис банківської операції."""

    id: str
    account_number: str
    operation: str
    amount: Money
    timestamp: datetime = field(default_factory=datetime.now)

    def __str__(self) -> str:
        time_str = self.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        return (
            f"[{time_str}] {self.id}: {self.operation.upper()} "
            f"{self.amount} on {self.account_number}"
        )


class Account(ABC):
    """Базовий абстрактний клас банківського рахунку (Entity)."""

    def __init__(
        self,
        account_number: str,
        customer: Customer,
        initial_balance: Money,
    ) -> None:
        if not account_number.strip():
            raise ValueError("Номер рахунку не може бути порожнім")
        self._account_number = account_number
        self._customer = customer
        self._balance = initial_balance
        self._transactions: list[Transaction] = []

    @property
    def id(self) -> str:
        return self._account_number

    @property
    def account_number(self) -> str:
        return self._account_number

    @property
    def customer(self) -> Customer:
        return self._customer

    @property
    def balance(self) -> Money:
        return self._balance

    @property
    def transactions(self) -> tuple[Transaction, ...]:
        return tuple(self._transactions)

    def deposit(self, amount: Money) -> Transaction:
        """Поповнення рахунку."""
        if amount.amount <= 0:
            raise ValueError("Сума поповнення повинна бути більшою за 0")
        self._balance = self._balance + amount
        tx = Transaction(
            id=f"TX-{len(self._transactions) + 1:04d}",
            account_number=self._account_number,
            operation="deposit",
            amount=amount,
        )
        self._transactions.append(tx)
        return tx

    @abstractmethod
    def withdraw(self, amount: Money) -> Transaction:
        """Зняття коштів з контролем заборони від'ємного балансу."""
        ...

    def __bool__(self) -> bool:
        return True

    def __len__(self) -> int:
        return len(self._transactions)

    def __iter__(self) -> Iterator[Transaction]:
        return iter(self._transactions)

    def __contains__(self, tx_id: object) -> bool:
        if not isinstance(tx_id, str):
            return False
        return any(tx.id == tx_id for tx in self._transactions)

    def __str__(self) -> str:
        cls_name = self.__class__.__name__
        return (
            f"{cls_name}({self._account_number}, "
            f"{self._customer.name}): {self._balance}"
        )

    def __repr__(self) -> str:
        cls_name = self.__class__.__name__
        return (
            f"{cls_name}(account_number={self._account_number!r}, "
            f"customer_id={self._customer.id}, balance={self._balance!r})"
        )


class SavingsAccount(Account):
    """Ощадний рахунок із відсотковою ставкою та незнижуваним залишком."""

    def __init__(
        self,
        account_number: str,
        customer: Customer,
        initial_balance: Money,
        interest_rate: float = 0.05,
        minimum_balance: Money | None = None,
    ) -> None:
        super().__init__(account_number, customer, initial_balance)
        if interest_rate < 0:
            raise ValueError("Відсоткова ставка не може бути від'ємною")
        self._interest_rate = interest_rate
        self._minimum_balance = (
            minimum_balance
            if minimum_balance is not None
            else Money(0.0, initial_balance.currency)
        )
        if initial_balance < self._minimum_balance:
            raise ValueError(
                "Початковий баланс нижчий за мінімально дозволений"
            )

    @property
    def interest_rate(self) -> float:
        return self._interest_rate

    @property
    def minimum_balance(self) -> Money:
        return self._minimum_balance

    def withdraw(self, amount: Money) -> Transaction:
        if amount.amount <= 0:
            raise ValueError("Сума зняття повинна бути більшою за 0")
        if self._balance < amount:
            raise ValueError(
                f"Недостатньо коштів: баланс {self._balance} < суми {amount}"
            )
        new_balance = self._balance - amount
        if new_balance < self._minimum_balance:
            msg = (
                f"Зняття заборонено: залишок {new_balance} "
                f"буде нижчим за ліміт {self._minimum_balance}"
            )
            raise ValueError(msg)
        self._balance = new_balance
        tx = Transaction(
            id=f"TX-{len(self._transactions) + 1:04d}",
            account_number=self._account_number,
            operation="withdraw",
            amount=amount,
        )
        self._transactions.append(tx)
        return tx

    def apply_interest(self) -> Transaction:
        """Нараховує відсотки на поточний залишок."""
        interest_amount = self._balance * self._interest_rate
        if interest_amount.amount > 0:
            self._balance = self._balance + interest_amount
            tx = Transaction(
                id=f"TX-{len(self._transactions) + 1:04d}",
                account_number=self._account_number,
                operation="interest",
                amount=interest_amount,
            )
            self._transactions.append(tx)
            return tx
        return Transaction(
            id=f"TX-{len(self._transactions) + 1:04d}",
            account_number=self._account_number,
            operation="interest",
            amount=Money(0.0, self._balance.currency),
        )


class CurrentAccount(Account):
    """Поточний рахунок із застосуванням політики комісій."""

    def __init__(
        self,
        account_number: str,
        customer: Customer,
        initial_balance: Money,
        fee_policy: FeePolicy | None = None,
    ) -> None:
        super().__init__(account_number, customer, initial_balance)
        self._fee_policy = (
            fee_policy if fee_policy is not None else ZeroFeePolicy()
        )

    @property
    def fee_policy(self) -> FeePolicy:
        return self._fee_policy

    def withdraw(self, amount: Money) -> Transaction:
        if amount.amount <= 0:
            raise ValueError("Сума зняття повинна бути більшою за 0")
        fee = self._fee_policy.calculate_fee(amount)
        total_required = amount + fee
        if self._balance < total_required:
            msg = (
                f"Недостатньо коштів для зняття: необхідно {total_required} "
                f"(включно з комісією {fee}), а баланс {self._balance}"
            )
            raise ValueError(msg)
        self._balance = self._balance - total_required
        tx = Transaction(
            id=f"TX-{len(self._transactions) + 1:04d}",
            account_number=self._account_number,
            operation="withdraw",
            amount=amount,
        )
        self._transactions.append(tx)
        return tx


class BankRegistry:
    """Користувацький клас-колекція банківських рахунків."""

    def __init__(self) -> None:
        self._accounts: dict[str, Account] = {}

    def add(self, account: Account) -> None:
        if account.account_number in self._accounts:
            msg = f"Рахунок {account.account_number} вже зареєстровано"
            raise ValueError(msg)
        self._accounts[account.account_number] = account

    def get(self, account_number: str) -> Account | None:
        return self._accounts.get(account_number)

    def total_funds(self, currency: str = "UAH") -> Money:
        total = 0.0
        for acc in self._accounts.values():
            if acc.balance.currency == currency:
                total += acc.balance.amount
        return Money(round(total, 2), currency)

    def __len__(self) -> int:
        return len(self._accounts)

    def __getitem__(self, account_number: str) -> Account:
        if account_number not in self._accounts:
            raise KeyError(f"Рахунок {account_number} не знайдено")
        return self._accounts[account_number]

    def __iter__(self) -> Iterator[Account]:
        return iter(self._accounts.values())

    def __contains__(self, account_number: object) -> bool:
        if not isinstance(account_number, str):
            return False
        return account_number in self._accounts
