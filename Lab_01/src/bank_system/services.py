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


def calculate_total_funds(accounts: list[Account]) -> float:
    return sum(account.balance for account in accounts)


def calculate_average_balance(accounts: list[Account]) -> float:
    if not accounts:
        return 0.0
    return calculate_total_funds(accounts) / len(accounts)


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