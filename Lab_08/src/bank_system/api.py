"""Асинхронний REST API банківської системи на базі FastAPI (Варіант 4)."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import httpx
from fastapi import Depends, FastAPI, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from .database import init_db
from .dependencies import get_session
from .exceptions import (
    AccountNotFoundError,
    AccountValidationError,
    DatabaseOperationError,
    InsufficientFundsError,
    InvalidAmountError,
)
from .external_api import fetch_many_accounts
from .models import Account, Client, Transaction
from .repositories import AccountRepository, ClientRepository, TransactionRepository
from .schemas import (
    AccountCreate,
    AccountResponse,
    AccountSummaryBatchItem,
    AccountUpdate,
    AmountOperation,
    BankStatisticsResponse,
    BatchAccountsRequest,
    ClientCreate,
    ClientResponse,
    ClientTotalItem,
    TransactionResponse,
    TransferRequest,
    TransferResponse,
)
from .services import BankService


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Ініціалізувати таблиці БД при старті застосунку."""
    init_db()
    yield


app = FastAPI(
    title="Bank System REST API",
    version="0.8.0",
    description=(
        "Асинхронний REST API системи банківських рахунків "
        "(Лабораторна робота №8, Варіант 4)."
    ),
    lifespan=lifespan,
)


@app.exception_handler(AccountNotFoundError)
async def account_not_found_handler(
    _request: Request,
    exc: Exception,
) -> JSONResponse:
    """Повернути 404 Not Found при відсутності рахунку чи клієнта."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc)},
    )


@app.exception_handler(InsufficientFundsError)
@app.exception_handler(InvalidAmountError)
@app.exception_handler(AccountValidationError)
async def validation_domain_error_handler(
    _request: Request,
    exc: Exception,
) -> JSONResponse:
    """Повернути 400 Bad Request при порушенні бізнес-правил суми або балансу."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)},
    )


@app.exception_handler(DatabaseOperationError)
async def database_conflict_handler(
    _request: Request,
    exc: Exception,
) -> JSONResponse:
    """Повернути 409 Conflict при порушенні унікальності чи обмежень БД."""
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": str(exc)},
    )


@app.get("/", tags=["Health"])
async def root() -> dict[str, str]:
    """Перевірка працездатності REST API."""
    return {"message": "Bank System API is running", "version": "0.8.0"}


@app.post(
    "/clients",
    response_model=ClientResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Clients"],
)
async def create_client(
    data: ClientCreate,
    session: Session = Depends(get_session),
) -> Client:
    """Зареєструвати нового клієнта банку."""
    repo = ClientRepository(session)
    return repo.add(full_name=data.full_name, email=data.email)


@app.get(
    "/clients",
    response_model=list[ClientResponse],
    tags=["Clients"],
)
async def list_clients(
    session: Session = Depends(get_session),
) -> list[Client]:
    """Отримати список усіх зареєстрованих клієнтів."""
    return ClientRepository(session).get_all()


@app.get(
    "/accounts/statistics",
    response_model=BankStatisticsResponse,
    tags=["Statistics"],
)
async def get_bank_statistics(
    session: Session = Depends(get_session),
) -> BankStatisticsResponse:
    """Отримати агреговану фінансову статистику банку."""
    service = BankService(session)
    accounts = AccountRepository(session).get_all()
    client_rows = service.get_client_totals()
    return BankStatisticsResponse(
        total_funds=service.get_total_funds(),
        average_balance=service.get_average_balance(),
        accounts_count=len(accounts),
        clients=[
            ClientTotalItem(
                full_name=full_name,
                total_balance=total_balance,
                accounts_count=accounts_count,
            )
            for full_name, total_balance, accounts_count in client_rows
        ],
    )


@app.post(
    "/accounts/batch",
    response_model=list[AccountSummaryBatchItem],
    tags=["Accounts"],
)
async def batch_accounts_summary(
    data: BatchAccountsRequest,
    max_concurrency: int = Query(default=3, ge=1, le=20),
    timeout_seconds: float = Query(default=5.0, gt=0.0, le=30.0),
) -> list[dict[str, Any]]:
    """Асинхронно отримати баланси та історію групи рахунків через HTTPX, Task і Semaphore."""
    transport = httpx.ASGITransport(app=app)
    try:
        return await fetch_many_accounts(
            base_url="http://bank-api.local",
            account_ids=data.account_ids,
            max_concurrency=max_concurrency,
            timeout_seconds=timeout_seconds,
            transport=transport,
        )
    except asyncio.TimeoutError as error:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Batch account loading timed out",
        ) from error
    except httpx.HTTPStatusError as error:
        raise HTTPException(
            status_code=error.response.status_code,
            detail=f"Downstream account request failed: {error.response.text}",
        ) from error


@app.get(
    "/accounts",
    response_model=list[AccountResponse],
    tags=["Accounts"],
)
async def list_accounts(
    client_id: int | None = Query(default=None, gt=0),
    account_type: str | None = Query(default=None),
    min_balance: float | None = Query(default=None, ge=0.0),
    search: str | None = Query(default=None),
    limit: int | None = Query(default=None, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
) -> list[Account]:
    """Отримати список рахунків з фільтрацією через query parameters та пагінацією."""
    return AccountRepository(session).search(
        client_id=client_id,
        account_type=account_type,
        min_balance=min_balance,
        search_query=search,
        limit=limit,
        offset=offset,
    )


@app.post(
    "/accounts",
    response_model=AccountResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Accounts"],
)
async def create_account(
    data: AccountCreate,
    session: Session = Depends(get_session),
) -> Account:
    """Відкрити новий банківський рахунок для існуючого клієнта."""
    client = ClientRepository(session).get_by_id(data.client_id)
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Client with id={data.client_id} not found",
        )
    account = Account(
        account_number=data.account_number,
        balance=data.balance,
        currency=data.currency,
        account_type=data.account_type,
        client_id=data.client_id,
    )
    return AccountRepository(session).add(account)


@app.get(
    "/accounts/{account_id}",
    response_model=AccountResponse,
    tags=["Accounts"],
)
async def get_account(
    account_id: int,
    session: Session = Depends(get_session),
) -> Account:
    """Отримати інформацію та поточний баланс рахунку за його ID."""
    account = AccountRepository(session).get_by_id(account_id)
    if account is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account id={account_id} not found",
        )
    return account


@app.patch(
    "/accounts/{account_id}",
    response_model=AccountResponse,
    tags=["Accounts"],
)
@app.put(
    "/accounts/{account_id}",
    response_model=AccountResponse,
    tags=["Accounts"],
)
async def update_account(
    account_id: int,
    data: AccountUpdate,
    session: Session = Depends(get_session),
) -> Account:
    """Оновити тип або валюту банківського рахунку."""
    updated = AccountRepository(session).update_attributes(
        account_id=account_id,
        account_type=data.account_type,
        currency=data.currency,
    )
    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account id={account_id} not found",
        )
    return updated


@app.delete(
    "/accounts/{account_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Accounts"],
)
async def delete_account(
    account_id: int,
    session: Session = Depends(get_session),
) -> None:
    """Видалити банківський рахунок за ідентифікатором."""
    deleted = AccountRepository(session).delete(account_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account id={account_id} not found",
        )


@app.get(
    "/accounts/{account_id}/transactions",
    response_model=list[TransactionResponse],
    tags=["Transactions"],
)
async def get_account_transactions(
    account_id: int,
    session: Session = Depends(get_session),
) -> list[Transaction]:
    """Отримати історію транзакцій для вказаного рахунку."""
    account = AccountRepository(session).get_by_id(account_id)
    if account is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account id={account_id} not found",
        )
    return TransactionRepository(session).get_by_account(account_id)


@app.post(
    "/accounts/{account_id}/deposit",
    response_model=AccountResponse,
    tags=["Operations"],
)
async def deposit_to_account(
    account_id: int,
    data: AmountOperation,
    session: Session = Depends(get_session),
) -> Account:
    """Поповнити банківський рахунок за його ID."""
    account = AccountRepository(session).get_by_id(account_id)
    if account is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account id={account_id} not found",
        )
    description = data.description or "Поповнення через REST API"
    return BankService(session).deposit(account.account_number, data.amount, description)


@app.post(
    "/accounts/{account_id}/withdraw",
    response_model=AccountResponse,
    tags=["Operations"],
)
async def withdraw_from_account(
    account_id: int,
    data: AmountOperation,
    session: Session = Depends(get_session),
) -> Account:
    """Зняти кошти з банківського рахунку за його ID (від'ємний баланс заборонений)."""
    account = AccountRepository(session).get_by_id(account_id)
    if account is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account id={account_id} not found",
        )
    description = data.description or "Зняття коштів через REST API"
    return BankService(session).withdraw(account.account_number, data.amount, description)


@app.post(
    "/transfers",
    response_model=TransferResponse,
    tags=["Operations"],
)
async def transfer_between_accounts(
    data: TransferRequest,
    session: Session = Depends(get_session),
) -> TransferResponse:
    """Виконати атомарний міжрахунковий переказ коштів із транзакційною фіксацією."""
    source, target = BankService(session).transfer_money(
        from_account_number=data.from_account_number,
        to_account_number=data.to_account_number,
        amount=data.amount,
    )
    return TransferResponse(
        source_account=AccountResponse.model_validate(source),
        target_account=AccountResponse.model_validate(target),
        transferred_amount=data.amount,
    )
