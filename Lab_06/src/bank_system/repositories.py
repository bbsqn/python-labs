"""Реалізація репозиторію банківських рахунків (Fake repository)."""

from .models import Account


class FakeAccountRepository:
    """In-Memory сховище банківських рахунків на базі словника."""

    def __init__(self) -> None:
        self._accounts: dict[str, Account] = {}

    def add(self, account: Account) -> None:
        """Зберегти або оновити рахунок."""
        self._accounts[account.account_number] = account

    def get(self, account_number: str) -> Account | None:
        """Отримати рахунок за номером або повернути None."""
        return self._accounts.get(account_number)

    def list_all(self) -> list[Account]:
        """Отримати копію списку всіх збережених рахунків."""
        return list(self._accounts.values())

    def total_funds(self) -> float:
        """Обчислити загальну суму коштів на всіх активних рахунках."""
        total = sum(acc.balance for acc in self._accounts.values() if acc.is_active)
        return round(total, 2)

    def __len__(self) -> int:
        """Повернути кількість збережених рахунків."""
        return len(self._accounts)

    def __contains__(self, account_number: str) -> bool:
        """Перевірити наявність рахунку за номером."""
        return account_number in self._accounts
