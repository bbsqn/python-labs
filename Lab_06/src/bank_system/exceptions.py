"""Ієрархія винятків банківської системи."""


class BankingError(Exception):
    """Базовий клас для всіх винятків банківської системи."""


class AccountValidationError(BankingError):
    """Помилка валідації банківського рахунку (номер, клієнт, початковий баланс)."""


class InsufficientFundsError(BankingError):
    """Спроба зняття коштів за умови недостатнього балансу."""


class InvalidAmountError(BankingError):
    """Некоректна сума операції (від'ємна або нульова)."""


class AccountNotFoundError(BankingError):
    """Запитуваний банківський рахунок не знайдено в репозиторії."""


class PaymentGatewayError(BankingError):
    """Помилка зовнішнього банківського шлюзу авторизації транзакцій."""


class NotificationError(BankingError):
    """Помилка надсилання сповіщення клієнту."""


class DataImportError(BankingError):
    """Помилка зчитування чи синтаксичного розбору вхідного CSV-файлу."""


class DataExportError(BankingError):
    """Помилка експорту банківських даних у формат JSON."""
