"""Точка входу програми банківської системи з SQLite, SQLAlchemy ORM та DB-API."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bank_system.database import SessionLocal, init_db  # noqa: E402
from bank_system.exceptions import BankingError  # noqa: E402
from bank_system.models import Account  # noqa: E402
from bank_system.repositories import (  # noqa: E402
    AccountRepository,
    ClientRepository,
    find_account_by_number_dbapi,
)
from bank_system.services import BankService  # noqa: E402


def main() -> None:
    """Демонстрація роботи persistence layer, ORM, транзакцій та DB-API."""
    init_db()

    with SessionLocal() as session:
        client_repo = ClientRepository(session)
        account_repo = AccountRepository(session)
        service = BankService(session)

        client1 = client_repo.get_by_name("Зінчук Остап")
        if client1 is None:
            client1 = client_repo.add("Зінчук Остап", email="ostap.zinchuk@example.com")

        client2 = client_repo.get_by_name("Коваль Анна")
        if client2 is None:
            client2 = client_repo.add("Коваль Анна", email="anna.koval@example.com")

        if account_repo.get_by_number("UA001") is None:
            account_repo.add(
                Account(
                    account_number="UA001",
                    balance=2500.0,
                    currency="UAH",
                    account_type="checking",
                    client_id=client1.id,
                )
            )
        if account_repo.get_by_number("UA002") is None:
            account_repo.add(
                Account(
                    account_number="UA002",
                    balance=1500.0,
                    currency="UAH",
                    account_type="savings",
                    client_id=client2.id,
                )
            )

        print("Рахунки до операцій:")
        for acc in account_repo.get_all():
            print(
                f"  [{acc.id}] {acc.account_number} | {acc.client_name:20} | "
                f"{acc.balance:10.2f} {acc.currency} ({acc.account_type})"
            )

        service.deposit("UA001", 500.0, "Премія")
        service.transfer_money("UA001", "UA002", 750.0)

        try:
            service.transfer_money("UA001", "UA_MISSING", 100.0)
        except BankingError as err:
            print(f"\nОчікуваний rollback транзакції при помилці: {err}")

        print(f"\nЗагальна сума коштів у банку: {service.get_total_funds():.2f} UAH")
        print(f"Середній баланс рахунку: {service.get_average_balance():.2f} UAH")

        print("\nАгрегація по клієнтах (JOIN + GROUP BY):")
        for full_name, total_sum, count in service.get_client_totals():
            print(f"  {full_name}: {total_sum:.2f} UAH (рахунків: {count})")

    db_rows = find_account_by_number_dbapi("bank_system.db", "UA001")
    print(f"\nРезультат параметризованого DB-API пошуку UA001: {db_rows}")


if __name__ == "__main__":
    main()
