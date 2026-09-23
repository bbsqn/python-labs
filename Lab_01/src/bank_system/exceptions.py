
class BankError(Exception):
    """Базовий клас для всіх помилок банківської системи."""


class NegativeAmountError(BankError):
    """Викидається, якщо сума поповнення/списання не є додатною."""


class InsufficientFundsError(BankError):
    """Викидається, якщо списання призвело б до від'ємного балансу."""


class AccountNotFoundError(BankError):
    """Викидається, якщо рахунок із заданим номером не знайдено."""