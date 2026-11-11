"""Ієрархія винятків банківської системи."""


class BankingError(Exception):
    """Базовий клас для всіх винятків банківської системи."""


BankError = BankingError


class AccountValidationError(BankingError, ValueError):
    """Помилка валідації банківського рахунку (номер, клієнт, початковий баланс)."""


class InsufficientFundsError(BankingError, ValueError):
    """Спроба зняття коштів за умови недостатнього балансу."""


class InvalidAmountError(BankingError, ValueError):
    """Некоректна сума операції (від'ємна або нульова)."""


NegativeAmountError = InvalidAmountError


class AccountNotFoundError(BankingError, KeyError):
    """Запитуваний банківський рахунок не знайдено в репозиторії."""


class PaymentGatewayError(BankingError, RuntimeError):
    """Помилка зовнішнього банківського шлюзу авторизації транзакцій."""


class NotificationError(BankingError, RuntimeError):
    """Помилка надсилання сповіщення клієнту."""


class DataImportError(BankingError, IOError):
    """Помилка зчитування чи синтаксичного розбору вхідного CSV-файлу."""


class DataExportError(BankingError, IOError):
    """Помилка експорту банківських даних у формат JSON."""
