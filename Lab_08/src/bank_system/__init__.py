"""Пакет банківської системи з асинхронним REST API на базі FastAPI (Lab 8)."""

from .api import app
from .database import DATABASE_URL, SessionLocal, create_sqlite_engine, engine, init_db
from .dependencies import get_session
from .exceptions import (
    AccountNotFoundError,
    AccountValidationError,
    BankError,
    BankingError,
    DatabaseOperationError,
    InsufficientFundsError,
    InvalidAmountError,
    NegativeAmountError,
)
from .external_api import fetch_account_summary, fetch_many_accounts, fetch_with_retry
from .models import Account, BankAccount, Base, Client, Transaction
from .repositories import (
    AccountRepository,
    ClientRepository,
    TransactionRepository,
    find_account_by_number_dbapi,
)
from .schemas import (
    AccountCreate,
    AccountResponse,
    AccountUpdate,
    AmountOperation,
    BankStatisticsResponse,
    BatchAccountsRequest,
    ClientCreate,
    ClientResponse,
    TransactionResponse,
    TransferRequest,
    TransferResponse,
)
from .services import BankingService, BankService, transfer_money

__all__ = [
    "Account",
    "AccountCreate",
    "AccountNotFoundError",
    "AccountRepository",
    "AccountResponse",
    "AccountUpdate",
    "AccountValidationError",
    "AmountOperation",
    "BankAccount",
    "BankError",
    "BankService",
    "BankStatisticsResponse",
    "BankingError",
    "BankingService",
    "Base",
    "BatchAccountsRequest",
    "Client",
    "ClientCreate",
    "ClientRepository",
    "ClientResponse",
    "DATABASE_URL",
    "DatabaseOperationError",
    "InsufficientFundsError",
    "InvalidAmountError",
    "NegativeAmountError",
    "SessionLocal",
    "Transaction",
    "TransactionRepository",
    "TransactionResponse",
    "TransferRequest",
    "TransferResponse",
    "app",
    "create_sqlite_engine",
    "engine",
    "fetch_account_summary",
    "fetch_many_accounts",
    "fetch_with_retry",
    "find_account_by_number_dbapi",
    "get_session",
    "init_db",
    "transfer_money",
]
