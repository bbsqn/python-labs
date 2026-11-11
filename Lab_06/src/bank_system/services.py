"""Сервіси бізнес-логіки банківських операцій та асинхронного шлюзу."""

from .exceptions import AccountNotFoundError, PaymentGatewayError
from .protocols import AccountRepository, AsyncBankingClient, Notifier


class BankingService:
    """Сервіс керування банківськими рахунками, транзакціями та клієнтськими сповіщеннями."""

    def __init__(
        self,
        repository: AccountRepository,
        notifier: Notifier,
    ) -> None:
        self.repository = repository
        self.notifier = notifier

    def process_deposit(
        self,
        account_number: str,
        amount: float,
        recipient: str,
    ) -> float:
        """Виконати операцію поповнення рахунку та надіслати клієнтське сповіщення."""
        account = self.repository.get(account_number)
        if account is None:
            raise AccountNotFoundError(
                f"Рахунок {account_number} не знайдено."
            )

        new_balance = account.deposit(amount)
        msg = (
            f"Поповнення рахунку {account_number} на суму {amount:.2f} грн успішне. "
            f"Баланс: {new_balance:.2f} грн."
        )
        self.notifier.send(recipient, msg)
        return new_balance

    def process_withdrawal(
        self,
        account_number: str,
        amount: float,
        recipient: str,
    ) -> float:
        """Виконати операцію зняття коштів та надіслати клієнтське сповіщення."""
        account = self.repository.get(account_number)
        if account is None:
            raise AccountNotFoundError(
                f"Рахунок {account_number} не знайдено."
            )

        new_balance = account.withdraw(amount)
        msg = (
            f"Зняття з рахунку {account_number} на суму {amount:.2f} грн успішне. "
            f"Баланс: {new_balance:.2f} грн."
        )
        self.notifier.send(recipient, msg)
        return new_balance

    def transfer(
        self,
        from_account_number: str,
        to_account_number: str,
        amount: float,
        sender_recipient: str,
    ) -> tuple[float, float]:
        """Міжбанківський або внутрішній переказ між двома рахунками."""
        source = self.repository.get(from_account_number)
        if source is None:
            raise AccountNotFoundError(
                f"Рахунок відправника {from_account_number} не знайдено."
            )

        target = self.repository.get(to_account_number)
        if target is None:
            raise AccountNotFoundError(
                f"Рахунок одержувача {to_account_number} не знайдено."
            )

        source.withdraw(amount)
        target.deposit(amount)

        self.notifier.send(
            sender_recipient,
            f"Переказ {amount:.2f} грн на рахунок {to_account_number} виконано успішно.",
        )
        return source.balance, target.balance

    def get_account_balance(self, account_number: str) -> float:
        """Перевірити поточний залишок на рахунку."""
        account = self.repository.get(account_number)
        if account is None:
            raise AccountNotFoundError(
                f"Рахунок {account_number} не знайдено."
            )
        return account.balance

    def calculate_total_funds(self) -> float:
        """Отримати загальну суму коштів у системі."""
        return self.repository.total_funds()


class AsyncBankingGateway:
    """Асинхронний платіжний шлюз для взаємодії зі сторонніми банківськими системами."""

    def __init__(self, client: AsyncBankingClient) -> None:
        self._client = client

    async def verify_transaction(
        self,
        account_number: str,
        amount: float,
    ) -> str:
        """Асинхронна авторизація транзакції у зовнішньому процесинговому центрі."""
        response = await self._client.authorize(account_number, amount)
        status = response.get("status", "REJECTED")

        if status != "APPROVED":
            raise PaymentGatewayError(
                f"Зовнішній банківський шлюз відхилив транзакцію: {status}"
            )
        return status
