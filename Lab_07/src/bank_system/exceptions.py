"""Ієрархія винятків банківської системи та шару збереження даних."""


class BankingError(Exception):
    """Базовий клас винятків банківської системи."""


BankError = BankingError


class AccountValidationError(BankingError, ValueError):
    """Помилка валідації реквізитів клієнта або рахунку."""


class InsufficientFundsError(BankingError, ValueError):
    """Спроба операції, що призводить до від'ємного балансу."""


class InvalidAmountError(BankingError, ValueError):
    """Некоректна сума операції (менша або рівна нулю)."""


NegativeAmountError = InvalidAmountError


class AccountNotFoundError(BankingError, KeyError):
    """Запитуваний банківський рахунок не знайдено у базі даних."""


class DatabaseOperationError(BankingError, RuntimeError):
    """Помилка транзакції або порушення обмежень цілісності БД."""
