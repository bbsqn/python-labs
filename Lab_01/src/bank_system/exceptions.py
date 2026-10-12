"""Винятки банківської системи."""


class BankError(Exception):
    """Базовий клас для всіх помилок банківської системи."""


class NegativeAmountError(BankError, ValueError):
    """Викидається, якщо сума поповнення/списання не є додатною."""


class InsufficientFundsError(BankError, ValueError):
    """Викидається, якщо списання призвело б до від'ємного балансу."""


class AccountNotFoundError(BankError, KeyError):
    """Викидається, якщо рахунок із заданим номером не знайдено."""
