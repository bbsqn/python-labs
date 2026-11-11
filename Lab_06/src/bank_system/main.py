"""Головна точка входу для демонстрації банківської системи (Lab_06)."""

import sys
from pathlib import Path

# Add src to sys.path when executed directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bank_system.models import Account  # noqa: E402
from bank_system.repositories import FakeAccountRepository  # noqa: E402
from bank_system.services import BankingService  # noqa: E402


class ConsoleNotifier:
    """Консольний сповіщувач для демонстрації."""

    def send(self, recipient: str, message: str) -> None:
        print(f"[Сповіщення -> {recipient}]: {message}")


def main() -> None:
    """Головна функція демонстрації роботи системи."""
    repo = FakeAccountRepository()
    notifier = ConsoleNotifier()
    service = BankingService(repository=repo, notifier=notifier)

    acc = Account("UA10000001", "Зінчук Остап", 1000.0)
    repo.add(acc)
    print(f"Створено рахунок: {acc.account_number}, баланс: {acc.balance} грн")

    service.process_deposit("UA10000001", 500.0, "ostap@example.com")
    service.process_withdrawal("UA10000001", 200.0, "ostap@example.com")
    print(f"Підсумковий залишок: {service.get_account_balance('UA10000001')} грн")


if __name__ == "__main__":
    main()
