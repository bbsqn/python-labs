"""Інтерфейсні протоколи для репозиторію, сповіщувача та зовнішнього шлюзу."""

from typing import Protocol

from .models import Account


class AccountRepository(Protocol):
    """Протокол сховища банківських рахунків."""

    def add(self, account: Account) -> None:
        """Додати новий рахунок до сховища."""
        ...

    def get(self, account_number: str) -> Account | None:
        """Знайти рахунок за його унікальним номером."""
        ...

    def list_all(self) -> list[Account]:
        """Повернути список усіх зареєстрованих рахунків."""
        ...

    def total_funds(self) -> float:
        """Обчислити загальну суму коштів на всіх рахунках."""
        ...


class Notifier(Protocol):
    """Протокол сервісу надсилання сповіщень клієнтам."""

    def send(self, recipient: str, message: str) -> None:
        """Надіслати повідомлення клієнту за контактною адресою/телефоном."""
        ...


class AsyncBankingClient(Protocol):
    """Протокол клієнта зовнішнього асинхронного банківського провайдера."""

    async def authorize(
        self,
        account_number: str,
        amount: float,
    ) -> dict[str, str]:
        """Асинхронний запит авторизації транзакції у платіжному провайдері."""
        ...
