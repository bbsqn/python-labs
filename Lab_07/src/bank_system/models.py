"""ORM-моделі SQLAlchemy для таблиць clients, accounts та transactions."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, validates

from .exceptions import AccountValidationError, InsufficientFundsError, InvalidAmountError


def _utc_now() -> datetime:
    """Повернути поточний UTC-час без tzinfo для сумісності з SQLite."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Base(DeclarativeBase):
    """Базовий декларативний клас для всіх ORM-моделей."""


class Client(Base):
    """ORM-модель клієнта банку (таблиця clients)."""

    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)

    accounts: Mapped[list["Account"]] = relationship(
        back_populates="client",
        cascade="all, delete-orphan",
    )

    @validates("full_name")
    def _validate_full_name(self, _key: str, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise AccountValidationError("Ім'я клієнта не може бути порожнім.")
        return cleaned

    def __repr__(self) -> str:
        return f"Client(id={self.id!r}, full_name={self.full_name!r})"


class Account(Base):
    """ORM-модель банківського рахунку (таблиця accounts)."""

    __tablename__ = "accounts"
    __table_args__ = (
        CheckConstraint("balance >= 0", name="ck_accounts_balance_non_negative"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    balance: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="UAH")
    account_type: Mapped[str] = mapped_column(String(50), nullable=False, default="checking")
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=_utc_now,
    )
    client_id: Mapped[int] = mapped_column(
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
    )

    client: Mapped["Client"] = relationship(back_populates="accounts")
    transactions: Mapped[list["Transaction"]] = relationship(
        back_populates="account",
        cascade="all, delete-orphan",
    )

    @validates("account_number")
    def _validate_account_number(self, _key: str, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise AccountValidationError("Номер рахунку не може бути порожнім.")
        return cleaned

    @validates("balance")
    def _validate_balance(self, _key: str, value: float) -> float:
        numeric = float(value)
        if numeric < 0:
            raise InsufficientFundsError(
                f"Від'ємний баланс рахунку заборонено: {numeric:.2f}"
            )
        return round(numeric, 2)

    @property
    def client_name(self) -> str:
        """Повернути ім'я власника рахунку."""
        return self.client.full_name if self.client is not None else ""

    def check_balance(self) -> float:
        """Повернути поточний залишок на рахунку."""
        return self.balance

    def __repr__(self) -> str:
        return (
            f"Account(id={self.id!r}, account_number={self.account_number!r}, "
            f"balance={self.balance!r})"
        )


BankAccount = Account


class Transaction(Base):
    """ORM-модель фінансової операції по рахунку (таблиця transactions)."""

    __tablename__ = "transactions"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_transactions_amount_positive"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_id: Mapped[int] = mapped_column(
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
    )
    operation_type: Mapped[str] = mapped_column(String(30), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=_utc_now,
    )

    account: Mapped["Account"] = relationship(back_populates="transactions")

    @validates("amount")
    def _validate_amount(self, _key: str, value: float) -> float:
        numeric = float(value)
        if numeric <= 0:
            raise InvalidAmountError(
                f"Сума транзакції повинна бути додатною, отримано: {numeric:.2f}"
            )
        return round(numeric, 2)

    def __repr__(self) -> str:
        return (
            f"Transaction(id={self.id!r}, account_id={self.account_id!r}, "
            f"type={self.operation_type!r}, amount={self.amount!r})"
        )
