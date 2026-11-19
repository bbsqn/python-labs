"""Асинхронний HTTP-клієнт (HTTPX) з Semaphore, retry/backoff та timeout."""

from __future__ import annotations

import asyncio
from typing import Any

import httpx


async def fetch_with_retry(
    client: httpx.AsyncClient,
    url: str,
    attempts: int = 3,
    backoff_base: float = 0.05,
) -> Any:
    """Виконати асинхронний GET-запит з повторними спробами та експоненційною затримкою."""
    for attempt in range(1, attempts + 1):
        try:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as error:
            if error.response.status_code < 500 or attempt == attempts:
                raise
            await asyncio.sleep(backoff_base * (2 ** (attempt - 1)))
        except httpx.RequestError:
            if attempt == attempts:
                raise
            await asyncio.sleep(backoff_base * (2 ** (attempt - 1)))
    raise RuntimeError("Unexpected retry state")


async def fetch_account_summary(
    client: httpx.AsyncClient,
    base_url: str,
    account_id: int,
    semaphore: asyncio.Semaphore,
    attempts: int = 3,
    backoff_base: float = 0.05,
) -> dict[str, Any]:
    """Отримати інформацію про рахунок та історію транзакцій з обмеженням Semaphore."""
    async with semaphore:
        account_data, transactions_data = await asyncio.gather(
            fetch_with_retry(
                client,
                f"{base_url}/accounts/{account_id}",
                attempts=attempts,
                backoff_base=backoff_base,
            ),
            fetch_with_retry(
                client,
                f"{base_url}/accounts/{account_id}/transactions",
                attempts=attempts,
                backoff_base=backoff_base,
            ),
        )
        return {
            "account": account_data,
            "transactions_count": len(transactions_data),
            "transactions": transactions_data,
        }


async def fetch_many_accounts(
    base_url: str,
    account_ids: list[int],
    max_concurrency: int = 3,
    timeout_seconds: float = 5.0,
    attempts: int = 3,
    backoff_base: float = 0.05,
    transport: httpx.AsyncBaseTransport | None = None,
) -> list[dict[str, Any]]:
    """Паралельно завантажити баланси та історію кількох рахунків через Task і gather()."""
    semaphore = asyncio.Semaphore(max_concurrency)
    async with httpx.AsyncClient(
        timeout=timeout_seconds,
        transport=transport,
    ) as client:
        tasks = [
            asyncio.create_task(
                fetch_account_summary(
                    client=client,
                    base_url=base_url,
                    account_id=acc_id,
                    semaphore=semaphore,
                    attempts=attempts,
                    backoff_base=backoff_base,
                )
            )
            for acc_id in account_ids
        ]
        results = await asyncio.wait_for(
            asyncio.gather(*tasks),
            timeout=timeout_seconds,
        )
        return list(results)
