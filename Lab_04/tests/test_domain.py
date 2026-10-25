"""Модульні тести для перевірки об'єктно-орієнтованої моделі Lab 4."""

# flake8: noqa: E402
from pathlib import Path
import sys
import unittest

SRC_DIR = str(Path(__file__).resolve().parent.parent / "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from domain_app.dto import CustomerPayload
from domain_app.models import (
    Account,
    BankRegistry,
    CurrentAccount,
    Customer,
    PercentageFeePolicy,
    SavingsAccount,
    Transaction,
)
from domain_app.protocols import HasId, Notifier
from domain_app.repositories import InMemoryRepository
from domain_app.services import BankingService, ConsoleNotifier
from domain_app.value_objects import Money


class TestDomainModel(unittest.TestCase):
    """Тести для перевірки доменної моделі, ООП-структур та бізнес-правил."""

    def test_money_value_object(self) -> None:
        m1 = Money(100.0, "UAH")
        m2 = Money(50.0, "UAH")

        self.assertEqual(m1 + m2, Money(150.0, "UAH"))
        self.assertEqual(m1 - m2, Money(50.0, "UAH"))
        self.assertEqual(m2 * 2, Money(100.0, "UAH"))

        with self.assertRaises(ValueError):
            Money(-10.0)

        with self.assertRaises(ValueError):
            _ = m2 - m1

        m_usd = Money(50.0, "USD")
        with self.assertRaises(ValueError):
            _ = m1 + m_usd

        self.assertTrue(m2 < m1)
        self.assertEqual(str(m1), "100.00 UAH")

    def test_customer_and_transaction(self) -> None:
        customer = Customer(id=1, name="Іван Франко", email="ivan@example.com")
        self.assertEqual(customer.display_name, "Іван Франко <ivan@example.com>")

        tx = Transaction("TX-001", "UA01", "deposit", Money(500.0))
        self.assertEqual(tx.id, "TX-001")
        self.assertIn("TX-001", str(tx))

    def test_savings_account_rules(self) -> None:
        customer = Customer(id=1, name="Остап", email="ostap@example.com")
        acc = SavingsAccount(
            account_number="UA001_SAVINGS",
            customer=customer,
            initial_balance=Money(2000.0),
            interest_rate=0.10,
            minimum_balance=Money(500.0),
        )

        self.assertEqual(acc.balance, Money(2000.0))
        self.assertEqual(acc.id, "UA001_SAVINGS")

        tx = acc.withdraw(Money(1000.0))
        self.assertEqual(acc.balance, Money(1000.0))
        self.assertEqual(tx.operation, "withdraw")

        with self.assertRaises(ValueError):
            acc.withdraw(Money(600.0))

        acc.apply_interest()
        self.assertEqual(acc.balance, Money(1100.0))

    def test_current_account_and_fee_policy(self) -> None:
        customer = Customer(id=2, name="Олена", email="olena@example.com")
        fee_policy = PercentageFeePolicy(percent=2.0)
        acc = CurrentAccount(
            account_number="UA002_CURRENT",
            customer=customer,
            initial_balance=Money(1000.0),
            fee_policy=fee_policy,
        )

        acc.withdraw(Money(500.0))
        self.assertEqual(acc.balance, Money(490.0))

        with self.assertRaises(ValueError):
            acc.withdraw(Money(500.0))

    def test_account_dunder_methods(self) -> None:
        customer = Customer(id=1, name="Тест", email="test@example.com")
        acc = SavingsAccount("UA01", customer, Money(1000.0))
        acc.deposit(Money(200.0))
        acc.withdraw(Money(100.0))

        self.assertEqual(len(acc), 2)

        tx_id = acc.transactions[0].id
        self.assertTrue(tx_id in acc)
        self.assertFalse("NON_EXISTING" in acc)

        tx_list = list(acc)
        self.assertEqual(len(tx_list), 2)

    def test_bank_registry_collection(self) -> None:
        c = Customer(id=1, name="Тест", email="test@example.com")
        acc1 = SavingsAccount("UA01", c, Money(1000.0))
        acc2 = CurrentAccount("UA02", c, Money(2000.0))

        registry = BankRegistry()
        registry.add(acc1)
        registry.add(acc2)

        self.assertEqual(len(registry), 2)
        self.assertTrue("UA01" in registry)
        self.assertEqual(registry["UA02"], acc2)
        self.assertEqual(registry.total_funds(), Money(3000.0))

    def test_generic_repository(self) -> None:
        repo: InMemoryRepository[Customer] = InMemoryRepository()
        c = Customer(id=10, name="Анна", email="anna@example.com")
        repo.add(c)

        self.assertEqual(repo.count(), 1)
        self.assertEqual(repo.get(10), c)
        self.assertEqual(len(repo.all()), 1)
        self.assertTrue(repo.remove(10))
        self.assertIsNone(repo.get(10))

    def test_banking_service_with_dependency_injection(self) -> None:
        acc_repo: InMemoryRepository[Account] = InMemoryRepository()
        cust_repo: InMemoryRepository[Customer] = InMemoryRepository()
        notifier = ConsoleNotifier()

        service = BankingService(
            account_repository=acc_repo,
            customer_repository=cust_repo,
            notifier=notifier,
        )

        payload: CustomerPayload = {
            "id": 1,
            "name": "Василь Бойко",
            "email": "vasyl@example.com",
        }
        customer = service.register_customer(payload)
        self.assertEqual(customer.name, "Василь Бойко")

        _ = service.open_savings_account("SAV01", customer.id, Money(5000.0))
        _ = service.open_current_account("CUR01", customer.id, Money(3000.0))

        service.transfer("SAV01", "CUR01", Money(1500.0))
        self.assertEqual(service.get_balance("SAV01"), Money(3500.0))
        self.assertEqual(service.get_balance("CUR01"), Money(4500.0))

        self.assertEqual(service.calculate_total_funds(), Money(8000.0))
        self.assertGreater(len(notifier.sent_messages), 0)

    def test_protocols_conformance(self) -> None:
        c = Customer(id=1, name="C", email="c@example.com")
        self.assertTrue(isinstance(c, HasId))

        notifier = ConsoleNotifier()
        self.assertTrue(isinstance(notifier, Notifier))


if __name__ == "__main__":
    unittest.main()
