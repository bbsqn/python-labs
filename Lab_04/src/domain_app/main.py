"""Головний демонстраційний скрипт (Lab 4)."""

# flake8: noqa: E402
from pathlib import Path
import sys

SRC_DIR = str(Path(__file__).resolve().parent.parent)
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from domain_app.dto import CustomerPayload
from domain_app.models import (
    Account,
    BankRegistry,
    Customer,
    PercentageFeePolicy,
)
from domain_app.repositories import InMemoryRepository
from domain_app.services import BankingService, ConsoleNotifier
from domain_app.value_objects import Money


def main() -> None:
    """Демонстраційний сценарій об'єктної моделі системи рахунків."""
    print("=" * 65)
    print("Лабораторна робота №4: Професійне ООП та система типів Python")
    print("Предметна область: Система банківських рахунків (Варіант 4)")
    print("=" * 65)

    # 1. Ініціалізація інфраструктури (Dependency Injection)
    customer_repo: InMemoryRepository[Customer] = InMemoryRepository()
    account_repo: InMemoryRepository[Account] = InMemoryRepository()
    notifier = ConsoleNotifier()

    service = BankingService(
        account_repository=account_repo,
        customer_repository=customer_repo,
        notifier=notifier,
    )

    # 2. Реєстрація клієнтів через TypedDict DTO
    client_payload_1: CustomerPayload = {
        "id": 1,
        "name": "Остап Зінчук",
        "email": "ostap@example.com",
        "phone": "+380501234567",
    }
    client_payload_2: CustomerPayload = {
        "id": 2,
        "name": "Олена Коваль",
        "email": "olena@example.com",
    }

    c1 = service.register_customer(client_payload_1)
    c2 = service.register_customer(client_payload_2)
    print(f"\nЗареєстровано клієнтів: {c1.display_name}, {c2.display_name}")

    # 3. Відкриття ощадного та поточного рахунків
    savings_acc = service.open_savings_account(
        account_number="UA001_SAVINGS",
        customer_id=c1.id,
        initial_deposit=Money(5000.0),
        interest_rate=0.08,
        minimum_balance=Money(500.0),
    )

    fee_policy = PercentageFeePolicy(percent=1.0)
    current_acc = service.open_current_account(
        account_number="UA002_CURRENT",
        customer_id=c2.id,
        initial_deposit=Money(10000.0),
        fee_policy=fee_policy,
    )

    print(f"\nВідкрито рахунки:")
    print(f"  -> {savings_acc}")
    print(f"  -> {current_acc}")

    # 4. Демонстрація операцій deposit та withdraw
    print("\n--- Виконання банківських операцій ---")
    service.deposit("UA001_SAVINGS", Money(1500.0))
    service.withdraw("UA002_CURRENT", Money(2000.0))

    # 5. Демонстрація захисту від від'ємного балансу
    print("\n--- Перевірка захисту від від'ємного балансу ---")
    try:
        service.withdraw("UA001_SAVINGS", Money(7000.0))
    except ValueError as exc:
        print(f"[Очікуване виключення]: {exc}")

    # 6. Нарахування відсотків на ощадний рахунок
    print("\n--- Нарахування річних відсотків ---")
    interest_tx = savings_acc.apply_interest()
    print(
        f"Нараховано відсотків: {interest_tx.amount} | "
        f"Новий баланс: {savings_acc.balance}"
    )

    # 7. Демонстрація міжбанківського переказу
    print("\n--- Міжбанківський переказ ---")
    service.transfer("UA002_CURRENT", "UA001_SAVINGS", Money(1000.0))

    # 8. Демонстрація Dunder методів на Account
    print("\n--- Перевірка dunder-методів (__len__, __iter__, __contains__) ---")
    print(f"Кількість операцій на рахунку UA001_SAVINGS: {len(savings_acc)}")
    first_tx_id = savings_acc.transactions[0].id
    print(
        f"Чи містить рахунок транзакцію {first_tx_id}: "
        f"{first_tx_id in savings_acc}"
    )
    print("Список усіх транзакцій рахунку:")
    for tx in savings_acc:
        print(f"   {tx}")

    # 9. Демонстрація кастомної колекції BankRegistry
    registry = BankRegistry()
    registry.add(savings_acc)
    registry.add(current_acc)
    print(f"\nРеєстр рахунків BankRegistry (кількість: {len(registry)}):")
    print(f"Рахунок UA001_SAVINGS через __getitem__: {registry['UA001_SAVINGS']}")
    print(f"Загальні кошти в системі: {service.calculate_total_funds()}")

    print("\n" + "=" * 65)
    print("Демонстраційний сценарій успішно виконано.")
    print("=" * 65)


if __name__ == "__main__":
    main()
