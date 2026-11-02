"""Ієрархія користувацьких винятків (Custom Exception Hierarchy)."""


class ApplicationError(Exception):
    """Базовий виняток додатку."""


class ConfigurationError(ApplicationError):
    """Помилка конфігураційного файлу або параметрів."""


class DataError(ApplicationError):
    """Базовий клас для помилок даних."""


class DataImportError(DataError):
    """Критична помилка процесу імпорту."""


class RecordValidationError(DataError):
    """Помилка валідації окремого запису таблиці."""

    def __init__(
        self,
        message: str,
        *,
        line_number: int | None = None,
        field: str | None = None,
    ) -> None:
        super().__init__(message)
        self.line_number = line_number
        self.field = field


class DataExportError(DataError):
    """Помилка процесу експорту."""


class BankingError(ApplicationError):
    """Базовий виняток для банківських операцій."""


class InsufficientFundsError(BankingError):
    """Спроба зняття коштів за відсутності достатнього балансу."""

    def __init__(
        self,
        account_number: str,
        balance: float,
        amount: float,
    ) -> None:
        message = (
            f"Недостатньо коштів на рахунку {account_number}: "
            f"баланс={balance:.2f}, потрібно={amount:.2f}"
        )
        super().__init__(message)
        self.account_number = account_number
        self.balance = balance
        self.amount = amount


class AccountNotFoundError(BankingError):
    """Рахунок із зазначеним номером не знайдено."""

    def __init__(self, account_number: str) -> None:
        super().__init__(f"Рахунок {account_number} не знайдено.")
        self.account_number = account_number


class InvalidTransactionError(BankingError):
    """Некоректні параметри транзакції (від'ємна сума тощо)."""


class NotificationDeliveryError(BankingError):
    """Збій доставки сповіщення клієнту або шлюзу."""
