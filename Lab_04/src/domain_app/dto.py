"""Модуль DTO та типізованих словників (TypedDict)."""

from typing import NotRequired, TypedDict


class CustomerPayload(TypedDict):
    """Зовнішній корисний вантаж даних клієнта."""

    id: int
    name: str
    email: str
    phone: NotRequired[str]


class AccountPayload(TypedDict):
    """Зовнішній корисний вантаж даних банківського рахунку."""

    account_number: str
    customer_id: int
    account_type: str
    initial_balance: float
    currency: NotRequired[str]


class TransactionPayload(TypedDict):
    """Зовнішній корисний вантаж запису транзакції."""

    id: str
    account_number: str
    operation: str
    amount: float
    currency: str
    timestamp: str
