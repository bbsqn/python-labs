"""Pydantic-схеми запитів, відповідей та валідації даних для REST API."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ClientCreate(BaseModel):
    """Схема створення клієнта банку."""

    full_name: str = Field(min_length=2, max_length=150)
    email: str | None = Field(default=None, max_length=255)


class ClientResponse(BaseModel):
    """Схема представлення клієнта у відповіді API."""

    id: int
    full_name: str
    email: str | None

    model_config = ConfigDict(from_attributes=True)


class AccountCreate(BaseModel):
    """Схема відкриття нового банківського рахунку."""

    account_number: str = Field(min_length=3, max_length=50)
    client_id: int = Field(gt=0)
    balance: float = Field(default=0.0, ge=0.0)
    currency: str = Field(default="UAH", min_length=3, max_length=10)
    account_type: str = Field(default="checking", min_length=2, max_length=50)


class AccountUpdate(BaseModel):
    """Схема часткового чи повного оновлення параметрів рахунку."""

    account_type: str | None = Field(default=None, min_length=2, max_length=50)
    currency: str | None = Field(default=None, min_length=3, max_length=10)


class AccountResponse(BaseModel):
    """Схема представлення банківського рахунку у відповіді API."""

    id: int
    account_number: str
    balance: float
    currency: str
    account_type: str
    client_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AmountOperation(BaseModel):
    """Схема операції поповнення або зняття коштів."""

    amount: float = Field(gt=0.0)
    description: str = Field(default="", max_length=255)


class TransferRequest(BaseModel):
    """Схема запиту на атомарний міжрахунковий переказ коштів."""

    from_account_number: str = Field(min_length=3, max_length=50)
    to_account_number: str = Field(min_length=3, max_length=50)
    amount: float = Field(gt=0.0)


class TransactionResponse(BaseModel):
    """Схема запису банківської транзакції."""

    id: int
    account_id: int
    operation_type: str
    amount: float
    description: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TransferResponse(BaseModel):
    """Схема результату атомарного переказу коштів."""

    source_account: AccountResponse
    target_account: AccountResponse
    transferred_amount: float


class ClientTotalItem(BaseModel):
    """Агрегована статистика рахунків одного клієнта."""

    full_name: str
    total_balance: float
    accounts_count: int


class BankStatisticsResponse(BaseModel):
    """Загальна фінансова статистика банківської системи."""

    total_funds: float
    average_balance: float
    accounts_count: int
    clients: list[ClientTotalItem]


class BatchAccountsRequest(BaseModel):
    """Запит на паралельне отримання стану та історії декількох рахунків."""

    account_ids: list[int] = Field(min_length=1)


class AccountSummaryBatchItem(BaseModel):
    """Зведений стан одного рахунку у пакетній відповіді."""

    account: AccountResponse
    transactions_count: int
    transactions: list[TransactionResponse]
