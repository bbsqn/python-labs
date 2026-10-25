"""Модуль сервісного рівня (Application / Service Layer)."""

from .dto import CustomerPayload
from .models import (
    Account,
    CurrentAccount,
    Customer,
    FeePolicy,
    SavingsAccount,
    Transaction,
)
from .protocols import Notifier
from .repositories import Repository
from .value_objects import Money


class ConsoleNotifier:
    """Адаптер сповіщень у консоль, що задовольняє Notifier Protocol."""

    def __init__(self) -> None:
        self.sent_messages: list[tuple[str, str]] = []

    def send(self, recipient: str, message: str) -> None:
        self.sent_messages.append((recipient, message))
        print(f"[NOTIFIER] До: {recipient} | Повідомлення: {message}")


class BankingService:
    """Оркестратор банківських операцій (Dependency Injection)."""

    def __init__(
        self,
        account_repository: Repository[Account],
        customer_repository: Repository[Customer],
        notifier: Notifier,
    ) -> None:
        self._accounts = account_repository
        self._customers = customer_repository
        self._notifier = notifier

    def register_customer(self, payload: CustomerPayload) -> Customer:
        """Реєструє клієнта на основі типізованого словника TypedDict."""
        customer = Customer(
            id=payload["id"],
            name=payload["name"],
            email=payload["email"],
            phone=payload.get("phone"),
        )
        self._customers.add(customer)
        self._notifier.send(
            customer.email,
            f"Вітаємо, {customer.name}! Ваш профіль успішно зареєстровано.",
        )
        return customer

    def open_savings_account(
        self,
        account_number: str,
        customer_id: int,
        initial_deposit: Money,
        interest_rate: float = 0.05,
        minimum_balance: Money | None = None,
    ) -> SavingsAccount:
        """Відкриває новий ощадний рахунок."""
        customer = self._customers.get(customer_id)
        if customer is None:
            raise ValueError(f"Клієнта з ID {customer_id} не знайдено")
        account = SavingsAccount(
            account_number=account_number,
            customer=customer,
            initial_balance=initial_deposit,
            interest_rate=interest_rate,
            minimum_balance=minimum_balance,
        )
        self._accounts.add(account)
        msg = (
            f"Відкрито ощадний рахунок {account_number} "
            f"із залишком {initial_deposit}"
        )
        self._notifier.send(customer.email, msg)
        return account

    def open_current_account(
        self,
        account_number: str,
        customer_id: int,
        initial_deposit: Money,
        fee_policy: FeePolicy | None = None,
    ) -> CurrentAccount:
        """Відкриває новий поточний рахунок."""
        customer = self._customers.get(customer_id)
        if customer is None:
            raise ValueError(f"Клієнта з ID {customer_id} не знайдено")
        account = CurrentAccount(
            account_number=account_number,
            customer=customer,
            initial_balance=initial_deposit,
            fee_policy=fee_policy,
        )
        self._accounts.add(account)
        msg = (
            f"Відкрито поточний рахунок {account_number} "
            f"із залишком {initial_deposit}"
        )
        self._notifier.send(customer.email, msg)
        return account

    def deposit(self, account_number: str, amount: Money) -> Transaction:
        """Здійснює поповнення рахунку."""
        account = self._accounts.get(account_number)
        if account is None:
            raise ValueError(f"Рахунок {account_number} не знайдено")
        tx = account.deposit(amount)
        msg = (
            f"Рахунок {account_number} поповнено на {amount}. "
            f"Баланс: {account.balance}"
        )
        self._notifier.send(account.customer.email, msg)
        return tx

    def withdraw(self, account_number: str, amount: Money) -> Transaction:
        """Здійснює зняття коштів з контролем від'ємного балансу."""
        account = self._accounts.get(account_number)
        if account is None:
            raise ValueError(f"Рахунок {account_number} не знайдено")
        tx = account.withdraw(amount)
        msg = (
            f"Знято {amount} з рахунку {account_number}. "
            f"Баланс: {account.balance}"
        )
        self._notifier.send(account.customer.email, msg)
        return tx

    def transfer(
        self,
        from_account_num: str,
        to_account_num: str,
        amount: Money,
    ) -> tuple[Transaction, Transaction]:
        """Виконує грошовий переказ між двома рахунками."""
        from_acc = self._accounts.get(from_account_num)
        to_acc = self._accounts.get(to_account_num)
        if from_acc is None:
            msg = f"Рахунок відправника {from_account_num} не знайдено"
            raise ValueError(msg)
        if to_acc is None:
            msg = f"Рахунок отримувача {to_account_num} не знайдено"
            raise ValueError(msg)

        tx_withdraw = from_acc.withdraw(amount)
        tx_deposit = to_acc.deposit(amount)

        msg_from = (
            f"Переказ {amount} на рахунок {to_account_num} успішний. "
            f"Баланс: {from_acc.balance}"
        )
        self._notifier.send(from_acc.customer.email, msg_from)

        msg_to = (
            f"Отримано переказ {amount} від {from_account_num}. "
            f"Баланс: {to_acc.balance}"
        )
        self._notifier.send(to_acc.customer.email, msg_to)
        return tx_withdraw, tx_deposit

    def get_balance(self, account_number: str) -> Money:
        """Повертає баланс рахунку."""
        account = self._accounts.get(account_number)
        if account is None:
            raise ValueError(f"Рахунок {account_number} не знайдено")
        return account.balance

    def find_account(self, account_number: str) -> Account | None:
        """Знаходить рахунок за номером."""
        return self._accounts.get(account_number)

    def calculate_total_funds(self, currency: str = "UAH") -> Money:
        """Підраховує загальну суму коштів на всіх рахунках."""
        total = 0.0
        for acc in self._accounts.all():
            if acc.balance.currency == currency:
                total += acc.balance.amount
        return Money(round(total, 2), currency)
