"""Бізнес-логіка банківської системи."""

from bank_system.config import MIN_BALANCE
from bank_system.exceptions import InsufficientFundsError, NegativeAmountError
from bank_system.models import Account


def find_account(
    accounts: list[Account],
    account_number: str,
) -> Account | None:
    for account in accounts:
        if account.account_number == account_number:
            return account
    return None


find_account_by_number = find_account
find_by_number = find_account
search_account = find_account


def find_accounts_by_client(
    accounts: list[Account],
    client_name: str,
) -> list[Account]:
    query = client_name.lower()
    return [
        account
        for account in accounts
        if query in account.client_name.lower()
    ]


find_by_client = find_accounts_by_client


def deposit(account: Account, amount: float) -> None:
    if amount <= 0:
        raise NegativeAmountError(
            "Сума поповнення повинна бути додатною."
        )
    account.balance += amount


def withdraw(account: Account, amount: float) -> None:
    if amount <= 0:
        raise NegativeAmountError(
            "Сума списання повинна бути додатною."
        )
    if account.balance - amount < MIN_BALANCE:
        raise InsufficientFundsError(
            f"Недостатньо коштів на рахунку {account.account_number}: "
            f"баланс {account.balance:.2f}, потрібно {amount:.2f}."
        )
    account.balance -= amount


def check_balance(account: Account) -> float:
    return account.balance


get_balance = check_balance


def calculate_total_funds(accounts: list[Account]) -> float:
    return sum(account.balance for account in accounts)


calculate_total_balance = calculate_total_funds
calculate_total = calculate_total_funds
total_funds = calculate_total_funds
get_total_funds = calculate_total_funds


def calculate_average_balance(accounts: list[Account]) -> float:
    if not accounts:
        return 0.0
    return calculate_total_funds(accounts) / len(accounts)


calculate_average_funds = calculate_average_balance


def sort_by_balance(
    accounts: list[Account],
    descending: bool = True,
) -> list[Account]:
    return sorted(
        accounts,
        key=lambda account: account.balance,
        reverse=descending,
    )


def find_richest_client(accounts: list[Account]) -> Account | None:
    if not accounts:
        return None
    return max(accounts, key=lambda account: account.balance)


get_richest_client = find_richest_client


def filter_by_balance(
    accounts: list[Account],
    min_balance: float = 0.0,
    max_balance: float | None = None,
) -> list[Account]:
    return [
        account
        for account in accounts
        if account.balance >= min_balance
        and (max_balance is None or account.balance <= max_balance)
    ]
