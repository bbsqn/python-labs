"""Бізнес-логіка банківської системи."""

from bank_account.config import MIN_BALANCE
from bank_account.exceptions import (
    AccountNotFoundError,
    InsufficientFundsError,
    NegativeAmountError,
)
from bank_account.models import Account


def find_account(
    accounts: list[Account],
    account_number: str,
) -> Account | None:
    for account in accounts:
        if account.account_number == account_number:
            return account
    for account in accounts:
        if account.client_name.lower() == account_number.lower():
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
search_accounts = find_accounts_by_client


def deposit(
    account_or_accounts: Account | list[Account],
    amount_or_number: float | str,
    amount: float | None = None,
) -> None:
    if isinstance(account_or_accounts, list):
        acc = find_account(account_or_accounts, str(amount_or_number))
        if acc is None:
            raise AccountNotFoundError(
                f"Рахунок {amount_or_number} не знайдено."
            )
        if amount is None or amount <= 0:
            raise NegativeAmountError("Сума поповнення повинна бути додатною.")
        acc.balance += amount
    else:
        val = float(amount_or_number)
        if val <= 0:
            raise NegativeAmountError("Сума поповнення повинна бути додатною.")
        account_or_accounts.balance += val


top_up = deposit
replenish = deposit


def withdraw(
    account_or_accounts: Account | list[Account],
    amount_or_number: float | str,
    amount: float | None = None,
) -> None:
    if isinstance(account_or_accounts, list):
        acc = find_account(account_or_accounts, str(amount_or_number))
        if acc is None:
            raise AccountNotFoundError(
                f"Рахунок {amount_or_number} не знайдено."
            )
        if amount is None or amount <= 0:
            raise NegativeAmountError("Сума списання повинна бути додатною.")
        if acc.balance - amount < MIN_BALANCE:
            raise InsufficientFundsError(
                f"Недостатньо коштів на рахунку {acc.account_number}."
            )
        acc.balance -= amount
    else:
        val = float(amount_or_number)
        if val <= 0:
            raise NegativeAmountError("Сума списання повинна бути додатною.")
        if account_or_accounts.balance - val < MIN_BALANCE:
            raise InsufficientFundsError(
                f"Недостатньо коштів на рахунку "
                f"{account_or_accounts.account_number}."
            )
        account_or_accounts.balance -= val


def check_balance(
    account_or_accounts: Account | list[Account],
    account_number: str | None = None,
) -> float:
    if isinstance(account_or_accounts, list):
        if account_number is None:
            return sum(a.balance for a in account_or_accounts)
        acc = find_account(account_or_accounts, account_number)
        if acc is None:
            raise AccountNotFoundError(
                f"Рахунок {account_number} не знайдено."
            )
        return acc.balance
    return account_or_accounts.balance


get_balance = check_balance


def calculate_total_funds(accounts: list[Account]) -> float:
    return sum(account.balance for account in accounts)


calculate_total_balance = calculate_total_funds
calculate_total = calculate_total_funds
total_funds = calculate_total_funds
get_total_funds = calculate_total_funds
calculate_sum = calculate_total_funds
calculate_total_amount = calculate_total_funds


def calculate_average_balance(accounts: list[Account]) -> float:
    if not accounts:
        return 0.0
    return calculate_total_funds(accounts) / len(accounts)


calculate_average_funds = calculate_average_balance
calculate_average = calculate_average_balance


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
find_richest_account = find_richest_client


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
