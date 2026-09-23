import unittest

from bank_system.exceptions import InsufficientFundsError, NegativeAmountError
from bank_system.models import Account
from bank_system.services import (
    calculate_average_balance,
    calculate_total_funds,
    deposit,
    find_account,
    find_richest_client,
    sort_by_balance,
    withdraw,
)


def make_accounts() -> list[Account]:
    return [
        Account("UA1", "Клієнт А", 100.0),
        Account("UA2", "Клієнт Б", 500.0),
    ]


class TestServices(unittest.TestCase):
    def test_deposit_increases_balance(self) -> None:
        account = Account("UA1", "Клієнт А", 100.0)
        deposit(account, 50.0)
        self.assertEqual(account.balance, 150.0)

    def test_deposit_rejects_negative_amount(self) -> None:
        account = Account("UA1", "Клієнт А", 100.0)
        with self.assertRaises(NegativeAmountError):
            deposit(account, -10.0)

    def test_withdraw_rejects_insufficient_funds(self) -> None:
        account = Account("UA1", "Клієнт А", 100.0)
        with self.assertRaises(InsufficientFundsError):
            withdraw(account, 200.0)

    def test_find_account_by_number(self) -> None:
        accounts = make_accounts()
        found = find_account(accounts, "UA2")
        self.assertIsNotNone(found)
        self.assertEqual(found.client_name, "Клієнт Б")

    def test_calculate_total_and_average(self) -> None:
        accounts = make_accounts()
        self.assertEqual(calculate_total_funds(accounts), 600.0)
        self.assertEqual(calculate_average_balance(accounts), 300.0)

    def test_sort_by_balance_descending(self) -> None:
        accounts = make_accounts()
        result = sort_by_balance(accounts)
        self.assertEqual(result[0].account_number, "UA2")

    def test_find_richest_client(self) -> None:
        accounts = make_accounts()
        richest = find_richest_client(accounts)
        self.assertIsNotNone(richest)
        self.assertEqual(richest.account_number, "UA2")


if __name__ == "__main__":
    unittest.main()
