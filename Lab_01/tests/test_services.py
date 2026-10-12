"""Тести для бізнес-логіки банківської системи."""

import unittest

from bank_system.exceptions import (

    InsufficientFundsError,

    NegativeAmountError,

)

from bank_system.models import Account, BankAccount

from bank_system.services import (

    calculate_average_balance,

    calculate_total_funds,

    check_balance,

    deposit,

    filter_by_balance,

    find_account,

    find_accounts_by_client,

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

        with self.assertRaises(ValueError):

            deposit(account, -10.0)

    def test_withdraw_decreases_balance(self) -> None:

        account = Account("UA1", "Клієнт А", 100.0)

        withdraw(account, 40.0)

        self.assertEqual(account.balance, 60.0)

    def test_withdraw_rejects_insufficient_funds(self) -> None:

        account = Account("UA1", "Клієнт А", 100.0)

        with self.assertRaises(InsufficientFundsError):

            withdraw(account, 200.0)

        with self.assertRaises(ValueError):

            withdraw(account, 200.0)

    def test_withdraw_rejects_negative_amount(self) -> None:

        account = Account("UA1", "Клієнт А", 100.0)

        with self.assertRaises(NegativeAmountError):

            withdraw(account, -10.0)

    def test_check_balance(self) -> None:

        account = Account("UA1", "Клієнт А", 123.45)

        self.assertEqual(check_balance(account), 123.45)

    def test_find_account_by_number(self) -> None:

        accounts = make_accounts()

        found = find_account(accounts, "UA2")

        self.assertIsNotNone(found)

        assert found is not None

        self.assertEqual(found.client_name, "Клієнт Б")

    def test_find_account_not_found(self) -> None:

        accounts = make_accounts()

        self.assertIsNone(find_account(accounts, "UNKNOWN"))

    def test_find_accounts_by_client(self) -> None:

        accounts = make_accounts()

        found = find_accounts_by_client(accounts, "клієнт а")

        self.assertEqual(len(found), 1)

        self.assertEqual(found[0].account_number, "UA1")

    def test_calculate_total_and_average(self) -> None:

        accounts = make_accounts()

        self.assertEqual(calculate_total_funds(accounts), 600.0)

        self.assertEqual(calculate_average_balance(accounts), 300.0)

    def test_calculate_average_empty(self) -> None:

        self.assertEqual(calculate_average_balance([]), 0.0)

    def test_sort_by_balance_descending(self) -> None:

        accounts = make_accounts()

        result = sort_by_balance(accounts)

        self.assertEqual(result[0].account_number, "UA2")

    def test_find_richest_client(self) -> None:

        accounts = make_accounts()

        richest = find_richest_client(accounts)

        self.assertIsNotNone(richest)

        assert richest is not None

        self.assertEqual(richest.account_number, "UA2")

    def test_filter_by_balance(self) -> None:

        accounts = make_accounts()

        filtered = filter_by_balance(accounts, min_balance=200.0)

        self.assertEqual(len(filtered), 1)

        self.assertEqual(filtered[0].account_number, "UA2")

    def test_account_alias_and_methods(self) -> None:

        account = BankAccount("UA3", "Клієнт В", 100.0)

        account.deposit(50.0)

        self.assertEqual(account.balance, 150.0)

        account.withdraw(50.0)

        self.assertEqual(account.balance, 100.0)

        self.assertEqual(account.check_balance(), 100.0)

        self.assertEqual(account.masked_number, "***UA3")


if __name__ == "__main__":

    unittest.main()
