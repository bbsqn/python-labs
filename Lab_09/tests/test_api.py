"""Автоматизовані синхронні та асинхронні тести REST API і HTTPX-клієнта."""

import asyncio
from typing import Any

import httpx
import pytest
from fastapi.testclient import TestClient

from bank_system.api import app
from bank_system.external_api import fetch_many_accounts, fetch_with_retry
from bank_system.models import Account, Client


def test_root_endpoint(client: TestClient) -> None:
    """Перевірка базового healthcheck endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "Bank System API is running"


def test_create_and_list_clients(client: TestClient) -> None:
    """Перевірка створення та перегляду клієнтів через REST API."""
    create_resp = client.post(
        "/clients",
        json={"full_name": "Шевченко Тарас", "email": "taras@example.com"},
    )
    assert create_resp.status_code == 201
    created = create_resp.json()
    assert created["full_name"] == "Шевченко Тарас"
    assert created["id"] > 0

    list_resp = client.get("/clients")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1


def test_create_account_and_conflicts(
    client: TestClient,
    seeded_accounts: tuple[Client, Client, Account, Account],
) -> None:
    """Перевірка POST /accounts, 404 для неіснуючого клієнта та 409 при дублікаті номера."""
    client_a, _, _, _ = seeded_accounts

    ok_resp = client.post(
        "/accounts",
        json={
            "account_number": "UA300003",
            "client_id": client_a.id,
            "balance": 750.0,
            "currency": "EUR",
            "account_type": "savings",
        },
    )
    assert ok_resp.status_code == 201
    assert ok_resp.json()["account_number"] == "UA300003"

    dup_resp = client.post(
        "/accounts",
        json={
            "account_number": "UA100001",
            "client_id": client_a.id,
            "balance": 100.0,
        },
    )
    assert dup_resp.status_code == 409

    missing_client_resp = client.post(
        "/accounts",
        json={"account_number": "UA999999", "client_id": 999999, "balance": 100.0},
    )
    assert missing_client_resp.status_code == 404


def test_get_account_and_query_filtering(
    client: TestClient,
    seeded_accounts: tuple[Client, Client, Account, Account],
) -> None:
    """Перевірка path parameter GET /accounts/{id} та query parameters GET /accounts."""
    _, _, acc_a, _ = seeded_accounts

    get_resp = client.get(f"/accounts/{acc_a.id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["account_number"] == "UA100001"

    missing_resp = client.get("/accounts/999999")
    assert missing_resp.status_code == 404

    filtered_resp = client.get("/accounts?account_type=savings&min_balance=400")
    assert filtered_resp.status_code == 200
    items = filtered_resp.json()
    assert len(items) == 1
    assert items[0]["account_number"] == "UA100002"


def test_patch_put_and_delete_account(
    client: TestClient,
    seeded_accounts: tuple[Client, Client, Account, Account],
) -> None:
    """Перевірка оновлення (PATCH/PUT) та видалення (DELETE) рахунку."""
    _, _, acc_a, _ = seeded_accounts

    patch_resp = client.patch(
        f"/accounts/{acc_a.id}",
        json={"account_type": "vip_checking"},
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["account_type"] == "vip_checking"

    put_resp = client.put(
        f"/accounts/{acc_a.id}",
        json={"account_type": "business", "currency": "USD"},
    )
    assert put_resp.status_code == 200
    assert put_resp.json()["currency"] == "USD"

    del_resp = client.delete(f"/accounts/{acc_a.id}")
    assert del_resp.status_code == 204
    assert client.get(f"/accounts/{acc_a.id}").status_code == 404
    assert client.delete(f"/accounts/{acc_a.id}").status_code == 404


def test_pydantic_validation_errors(
    client: TestClient,
    seeded_accounts: tuple[Client, Client, Account, Account],
) -> None:
    """Перевірка автоматичної Pydantic-валідації вхідних JSON-даних (422)."""
    client_a, _, acc_a, _ = seeded_accounts

    bad_account = client.post(
        "/accounts",
        json={"account_number": "UA555", "client_id": client_a.id, "balance": -100.0},
    )
    assert bad_account.status_code == 422

    bad_deposit = client.post(
        f"/accounts/{acc_a.id}/deposit",
        json={"amount": -50.0},
    )
    assert bad_deposit.status_code == 422


def test_deposit_withdraw_and_transactions_history(
    client: TestClient,
    seeded_accounts: tuple[Client, Client, Account, Account],
) -> None:
    """Перевірка поповнення, списання, заборони мінусу та історії транзакцій."""
    _, _, acc_a, _ = seeded_accounts

    dep_resp = client.post(
        f"/accounts/{acc_a.id}/deposit",
        json={"amount": 250.0, "description": "Поповнення"},
    )
    assert dep_resp.status_code == 200
    assert dep_resp.json()["balance"] == pytest.approx(1250.0)

    wdr_resp = client.post(
        f"/accounts/{acc_a.id}/withdraw",
        json={"amount": 200.0, "description": "Зняття"},
    )
    assert wdr_resp.status_code == 200
    assert wdr_resp.json()["balance"] == pytest.approx(1050.0)

    over_resp = client.post(
        f"/accounts/{acc_a.id}/withdraw",
        json={"amount": 5000.0},
    )
    assert over_resp.status_code == 400

    hist_resp = client.get(f"/accounts/{acc_a.id}/transactions")
    assert hist_resp.status_code == 200
    history = hist_resp.json()
    assert len(history) == 2
    assert [tx["operation_type"] for tx in history] == ["deposit", "withdraw"]


def test_atomic_transfers_and_statistics_endpoints(
    client: TestClient,
    seeded_accounts: tuple[Client, Client, Account, Account],
) -> None:
    """Перевірка POST /transfers (успіх і rollback при помилці) та GET /accounts/statistics."""
    transfer_resp = client.post(
        "/transfers",
        json={
            "from_account_number": "UA100001",
            "to_account_number": "UA100002",
            "amount": 300.0,
        },
    )
    assert transfer_resp.status_code == 200
    body = transfer_resp.json()
    assert body["source_account"]["balance"] == pytest.approx(700.0)
    assert body["target_account"]["balance"] == pytest.approx(800.0)

    fail_transfer = client.post(
        "/transfers",
        json={
            "from_account_number": "UA100001",
            "to_account_number": "UA_NON_EXISTENT",
            "amount": 100.0,
        },
    )
    assert fail_transfer.status_code == 404

    stats_resp = client.get("/accounts/statistics")
    assert stats_resp.status_code == 200
    stats = stats_resp.json()
    assert stats["total_funds"] == pytest.approx(1500.0)
    assert stats["average_balance"] == pytest.approx(750.0)
    assert stats["accounts_count"] == 2


@pytest.mark.asyncio
async def test_async_httpx_and_batch_endpoint(
    seeded_accounts: tuple[Client, Client, Account, Account],
) -> None:
    """Асинхронний тест FastAPI через httpx.AsyncClient + ASGITransport та /accounts/batch."""
    _, _, acc_a, acc_b = seeded_accounts
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as async_client:
        await async_client.post(
            f"/accounts/{acc_a.id}/deposit",
            json={"amount": 100.0},
        )
        batch_resp = await async_client.post(
            "/accounts/batch",
            json={"account_ids": [acc_a.id, acc_b.id]},
        )

    assert batch_resp.status_code == 200
    summaries = batch_resp.json()
    assert len(summaries) == 2
    assert summaries[0]["account"]["balance"] == pytest.approx(1100.0)
    assert summaries[0]["transactions_count"] == 1
    assert summaries[1]["account"]["balance"] == pytest.approx(500.0)


@pytest.mark.asyncio
async def test_external_api_retry_with_backoff() -> None:
    """Перевірка retry-логіки з експоненційною затримкою при тимчасових 503 помилках."""
    call_counter = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        call_counter["count"] += 1
        if call_counter["count"] < 3:
            return httpx.Response(status_code=503, json={"detail": "Temporary overload"})
        return httpx.Response(status_code=200, json={"status": "ok", "url": str(request.url)})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as mock_client:
        data: Any = await fetch_with_retry(
            mock_client,
            "http://mock-service/health",
            attempts=3,
            backoff_base=0.01,
        )

    assert call_counter["count"] == 3
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_external_api_timeout_enforced() -> None:
    """Перевірка спрацювання asyncio.TimeoutError при перевищенні часу очікування."""

    async def slow_handler(_request: httpx.Request) -> httpx.Response:
        await asyncio.sleep(0.3)
        return httpx.Response(status_code=200, json={"id": 1})

    transport = httpx.MockTransport(slow_handler)
    with pytest.raises(asyncio.TimeoutError):
        await fetch_many_accounts(
            base_url="http://mock-service",
            account_ids=[1, 2],
            max_concurrency=2,
            timeout_seconds=0.05,
            attempts=1,
            transport=transport,
        )
