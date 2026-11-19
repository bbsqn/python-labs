"""Демонстраційна точка входу та асинхронна перевірка REST API через HTTPX."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bank_system.api import app  # noqa: E402
from bank_system.database import SessionLocal, init_db  # noqa: E402
from bank_system.external_api import fetch_many_accounts  # noqa: E402
from bank_system.models import Account  # noqa: E402
from bank_system.repositories import AccountRepository, ClientRepository  # noqa: E402


async def run_async_api_demo() -> None:
    """Асинхронно продемонструвати роботу REST API та HTTPX з Semaphore."""
    init_db()

    with SessionLocal() as session:
        client_repo = ClientRepository(session)
        account_repo = AccountRepository(session)

        client1 = client_repo.get_by_name("Зінчук Остап")
        if client1 is None:
            client1 = client_repo.add("Зінчук Остап", email="ostap.zinchuk@example.com")

        client2 = client_repo.get_by_name("Коваль Анна")
        if client2 is None:
            client2 = client_repo.add("Коваль Анна", email="anna.koval@example.com")

        acc1 = account_repo.get_by_number("UA001")
        if acc1 is None:
            acc1 = account_repo.add(
                Account(
                    account_number="UA001",
                    balance=2500.0,
                    currency="UAH",
                    account_type="checking",
                    client_id=client1.id,
                )
            )
        acc2 = account_repo.get_by_number("UA002")
        if acc2 is None:
            acc2 = account_repo.add(
                Account(
                    account_number="UA002",
                    balance=1500.0,
                    currency="UAH",
                    account_type="savings",
                    client_id=client2.id,
                )
            )
        account_ids = [acc1.id, acc2.id]

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://bank-api.local",
        timeout=5.0,
    ) as client:
        root_resp = await client.get("/")
        print("GET / ->", root_resp.status_code, root_resp.json())

        deposit_resp = await client.post(
            f"/accounts/{account_ids[0]}/deposit",
            json={"amount": 300.0, "description": "Поповнення через HTTPX"},
        )
        print("POST /accounts/{id}/deposit ->", deposit_resp.status_code, deposit_resp.json())

        transfer_resp = await client.post(
            "/transfers",
            json={
                "from_account_number": "UA001",
                "to_account_number": "UA002",
                "amount": 200.0,
            },
        )
        print("POST /transfers ->", transfer_resp.status_code)

        stats_resp = await client.get("/accounts/statistics")
        print("GET /accounts/statistics ->", stats_resp.status_code, stats_resp.json())

    summaries = await fetch_many_accounts(
        base_url="http://bank-api.local",
        account_ids=account_ids,
        max_concurrency=2,
        timeout_seconds=5.0,
        transport=httpx.ASGITransport(app=app),
    )
    print(f"Паралельно завантажено рахунків через Semaphore + gather: {len(summaries)}")


def main() -> None:
    """Точка входу програми."""
    asyncio.run(run_async_api_demo())


if __name__ == "__main__":
    main()
