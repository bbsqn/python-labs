"""Конфігурація pytest та спільні фікстури для тестів."""

from collections.abc import Callable
from pathlib import Path
from unittest.mock import Mock

import pytest

from reliable_importer.models import (
    BankAccount,
    BankAccountRecord,
)
from reliable_importer.services import (
    BankingService,
    InMemoryAccountRepository,
    Notifier,
)


@pytest.fixture
def sample_account_row() -> dict[str, str]:
    """Фікстура коректного словника рядка банківської операції з CSV."""
    return {
        "account_number": "UA10000001",
        "client": "Остап Зінчук",
        "balance": "1500.50",
        "operation": "deposit",
        "amount": "200.00",
    }


@pytest.fixture
def sample_bank_account() -> BankAccount:
    """Фікстура стандартного доменного об'єкта банківського рахунку."""
    return BankAccount(
        account_number="UA10000001",
        client="Остап Зінчук",
        balance=1500.50,
    )


@pytest.fixture
def sample_record() -> BankAccountRecord:
    """Фікстура незмінного запису операції для експорту."""
    return BankAccountRecord(
        account_number="UA10000001",
        client="Остап Зінчук",
        balance=1500.50,
        operation="deposit",
        amount=200.00,
        new_balance=1700.50,
    )


@pytest.fixture
def in_memory_repo() -> InMemoryAccountRepository:
    """Фікстура In-Memory репозиторію з попередньо завантаженими рахунками."""
    repo = InMemoryAccountRepository()
    repo.add(BankAccount("UA10000001", "Остап Зінчук", 1500.50))
    repo.add(BankAccount("UA10000002", "Марія Коваль", 3200.00))
    repo.add(BankAccount("UA10000003", "Іван Франко", 500.00))
    return repo


@pytest.fixture
def mock_notifier() -> Mock:
    """Фікстура Mock-об'єкта для інтерфейсу сповіщувача."""
    notifier = Mock(spec=Notifier)
    notifier.notify.return_value = True
    return notifier


@pytest.fixture
def banking_service(
    in_memory_repo: InMemoryAccountRepository,
    mock_notifier: Mock,
) -> BankingService:
    """Фікстура банківського сервісу зі зв'язаними залежностями."""
    return BankingService(
        repository=in_memory_repo,
        notifier=mock_notifier,
    )


@pytest.fixture
def account_factory() -> Callable[..., BankAccount]:
    """Фабрична фікстура для динамічного створення рахунків з параметрами."""

    def _create_account(
        account_number: str = "UA99999999",
        client: str = "Тестовий Клієнт",
        balance: float = 1000.0,
    ) -> BankAccount:
        return BankAccount(
            account_number=account_number,
            client=client,
            balance=balance,
        )

    return _create_account


@pytest.fixture
def sample_records_list() -> list[BankAccountRecord]:
    """Фікстура списку записів для перевірки експорту."""
    return [
        BankAccountRecord(
            account_number="UA10000001",
            client="Остап Зінчук",
            balance=1500.50,
            operation="deposit",
            amount=200.00,
            new_balance=1700.50,
        ),
        BankAccountRecord(
            account_number="UA10000002",
            client="Марія Коваль",
            balance=3200.00,
            operation="withdraw",
            amount=500.00,
            new_balance=2700.00,
        ),
    ]


@pytest.fixture
def sample_csv_file(tmp_path: Path) -> Path:
    """Фікстура тимчасового валідного CSV файлу банківських операцій."""
    csv_file = tmp_path / "valid_accounts.csv"
    content = (
        "account_number,client,balance,operation,amount\n"
        "UA10000001,Остап Зінчук,1500.50,deposit,200.00\n"
        "UA10000002,Марія Коваль,3200.00,withdraw,500.00\n"
        "UA10000003,Іван Франко,450.00,deposit,150.00\n"
    )
    csv_file.write_text(content, encoding="utf-8")
    return csv_file


@pytest.fixture
def malformed_csv_file(tmp_path: Path) -> Path:
    """Фікстура тимчасового CSV файлу з некоректними записами."""
    csv_file = tmp_path / "malformed_accounts.csv"
    content = (
        "account_number,client,balance,operation,amount\n"
        "UA10000001,Остап Зінчук,1500.50,deposit,200.00\n"
        ",Невідомий Клієнт,500.00,deposit,100.00\n"
        "UA10000002,Марія Коваль,not_a_number,deposit,100.00\n"
        "UA10000003,Іван Франко,300.00,withdraw,100.00\n"
    )
    csv_file.write_text(content, encoding="utf-8")
    return csv_file


@pytest.fixture
def sample_config_yaml(tmp_path: Path, sample_csv_file: Path) -> Path:
    """Фікстура тимчасового коректного файлу конфігурації YAML."""
    config_file = tmp_path / "config.yaml"
    out_file = tmp_path / "output" / "accounts.json"
    log_file = tmp_path / "logs" / "test.log"
    content = (
        f"input:\n"
        f"  path: {sample_csv_file.as_posix()}\n"
        f"output:\n"
        f"  path: {out_file.as_posix()}\n"
        f"processing:\n"
        f"  minimum_balance: 100.0\n"
        f"  skip_invalid: true\n"
        f"logging:\n"
        f"  level: INFO\n"
        f"  path: {log_file.as_posix()}\n"
    )
    config_file.write_text(content, encoding="utf-8")
    return config_file
