"""Доменні моделі банківських рахунків та записів транзакцій."""

from dataclasses import asdict, dataclass

from .exceptions import AccountValidationError, InsufficientFundsError, InvalidAmountError


@dataclass(slots=True)
class Account:
    """Сутність банківського рахунку клієнта з підтримкою фінансових операцій."""

    account_number: str
    client: str
    balance: float = 0.0
    currency: str = "UAH"
    is_active: bool = True

    def __post_init__(self) -> None:
        """Перевірка обов'язкових полів та коректності початкового балансу."""
        if not self.account_number or not self.account_number.strip():
            raise AccountValidationError("Номер рахунку не може бути порожнім.")
        if not self.client or not self.client.strip():
            raise AccountValidationError("Ім'я клієнта не може бути порожнім.")
        if self.balance < 0:
            raise AccountValidationError(
                f"Початковий баланс не може бути від'ємним: {self.balance}"
            )
        self.account_number = self.account_number.strip()
        self.client = self.client.strip()
        self.balance = float(self.balance)

    def deposit(self, amount: float) -> float:
        """Поповнення рахунку на вказану суму."""
        if amount <= 0:
            raise InvalidAmountError(
                f"Сума поповнення повинна бути додатною, отримано: {amount}"
            )
        self.balance = round(self.balance + amount, 2)
        return self.balance

    def withdraw(self, amount: float) -> float:
        """Зняття коштів з рахунку з контролем достатності балансу."""
        if amount <= 0:
            raise InvalidAmountError(
                f"Сума зняття повинна бути додатною, отримано: {amount}"
            )
        if amount > self.balance:
            raise InsufficientFundsError(
                f"Недостатньо коштів на рахунку {self.account_number}: "
                f"доступно {self.balance:.2f}, запитано {amount:.2f}"
            )
        self.balance = round(self.balance - amount, 2)
        return self.balance

    def to_dict(self) -> dict[str, object]:
        """Серіалізація моделі рахунку в словник."""
        return {
            "account_number": self.account_number,
            "client": self.client,
            "balance": self.balance,
            "currency": self.currency,
            "is_active": self.is_active,
        }


@dataclass(frozen=True, slots=True)
class AccountRecord:
    """Незмінний запис для імпорту/експорту рахунків."""

    account_number: str
    client: str
    balance: float
    currency: str = "UAH"

    def to_dict(self) -> dict[str, object]:
        """Серіалізація запису."""
        return asdict(self)

