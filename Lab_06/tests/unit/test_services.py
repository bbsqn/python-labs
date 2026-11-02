"""Модульні тести бізнес-сервісів, репозиторію та асинхронного шлюзу."""

from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest

from reliable_importer.exceptions import (
    AccountNotFoundError,
    InsufficientFundsError,
    NotificationDeliveryError,
    RecordValidationError,
)
from reliable_importer.models import BankAccount, BankAccountRecord
from reliable_importer.services import (
    AsyncBankingGateway,
    BankingService,
    ImportStatistics,
    InMemoryAccountRepository,
    filter_by_balance,
    import_accounts,
)


def test_import_accounts_strict_mode(malformed_csv_file: Path) -> None:
    """У Strict режимі перша помилка валідації перериває імпорт."""
    stats = ImportStatistics()
    generator = import_accounts(
        malformed_csv_file,
        skip_invalid=False,
        statistics=stats,
    )
    first_record = next(generator)
    assert first_record.account_number == "UA10000001"

    with pytest.raises(RecordValidationError) as exc_info:
        next(generator)

    assert exc_info.value.field == "account_number"
    assert stats.total == 2
    assert stats.valid == 1
    assert stats.invalid == 1


def test_import_accounts_tolerant_mode(malformed_csv_file: Path) -> None:
    """У Tolerant режимі некоректні записи пропускаються без аварії."""
    stats = ImportStatistics()
    records = list(
        import_accounts(
            malformed_csv_file,
            skip_invalid=True,
            statistics=stats,
        )
    )
    assert len(records) == 2
    assert stats.total == 4
    assert stats.valid == 2
    assert stats.invalid == 2
    assert [r.account_number for r in records] == [
        "UA10000001",
        "UA10000003",
    ]


def test_filter_by_balance(
    sample_records_list: list[BankAccountRecord],
) -> None:
    """Перевірка фільтрації записів за мінімальним порогом балансу."""
    filtered = list(
        filter_by_balance(sample_records_list, minimum_balance=2000.0)
    )
    assert len(filtered) == 1
    assert filtered[0].account_number == "UA10000002"

    filtered_none = list(
        filter_by_balance(sample_records_list, minimum_balance=10000.0)
    )
    assert len(filtered_none) == 0


def test_in_memory_repository() -> None:
    """Перевірка CRUD операцій та підрахунку коштів у репозиторії."""
    repo = InMemoryAccountRepository()
    assert repo.list_all() == []
    assert repo.total_funds() == pytest.approx(0.0)

    acc1 = BankAccount("UA100", "Клієнт 1", 1000.0)
    acc2 = BankAccount("UA200", "Клієнт 2", 2500.50)
    repo.add(acc1)
    repo.add(acc2)

    assert repo.get("UA100") == acc1
    assert repo.get("UA200") == acc2
    assert repo.get("UNKNOWN") is None
    assert len(repo.list_all()) == 2
    assert repo.total_funds() == pytest.approx(3500.50)


def test_banking_service_create_account(
    banking_service: BankingService,
    mock_notifier: Mock,
) -> None:
    """Створення рахунку реєструє його в сховищі та надсилає сповіщення."""
    acc = banking_service.create_account(
        account_number="UA77700001",
        client="Тарас Шевченко",
        initial_balance=5000.0,
    )
    assert acc.account_number == "UA77700001"
    assert banking_service.get_balance("UA77700001") == pytest.approx(5000.0)

    mock_notifier.notify.assert_called_once_with(
        "UA77700001",
        "Рахунок UA77700001 успішно відкрито.",
    )


def test_banking_service_deposit_success(
    banking_service: BankingService,
    mock_notifier: Mock,
) -> None:
    """Поповнення рахунку оновлює баланс та викликає Notifier з аргументами."""
    new_bal = banking_service.deposit("UA10000001", 500.0)
    assert new_bal == pytest.approx(2000.50)
    assert banking_service.get_balance("UA10000001") == pytest.approx(2000.50)

    mock_notifier.notify.assert_called_once_with(
        "UA10000001",
        "Поповнення 500.00 грн. Баланс: 2000.50 грн.",
    )


def test_banking_service_deposit_account_not_found(
    banking_service: BankingService,
    mock_notifier: Mock,
) -> None:
    """Поповнення неіснуючого рахунку викликає AccountNotFoundError."""
    with pytest.raises(AccountNotFoundError) as exc_info:
        banking_service.deposit("NON_EXISTENT_ACC", 100.0)

    assert exc_info.value.account_number == "NON_EXISTENT_ACC"
    mock_notifier.notify.assert_not_called()


def test_banking_service_withdraw_success(
    banking_service: BankingService,
    mock_notifier: Mock,
) -> None:
    """Зняття коштів оновлює баланс та фіксує взаємодію з Mock сповіщувача."""
    new_bal = banking_service.withdraw("UA10000001", 500.50)
    assert new_bal == pytest.approx(1000.00)

    mock_notifier.notify.assert_called_once_with(
        "UA10000001",
        "Зняття 500.50 грн. Новий баланс: 1000.00 грн.",
    )


def test_banking_service_withdraw_insufficient_funds(
    banking_service: BankingService,
    mock_notifier: Mock,
) -> None:
    """При овердрафті транзакція блокується і сповіщення не відправляється."""
    with pytest.raises(InsufficientFundsError):
        banking_service.withdraw("UA10000001", 5000.00)

    assert banking_service.get_balance("UA10000001") == pytest.approx(1500.50)
    mock_notifier.notify.assert_not_called()


def test_banking_service_total_funds(
    banking_service: BankingService,
) -> None:
    """Перевірка обчислення загального обсягу коштів банку."""
    expected = 1500.50 + 3200.00 + 500.00
    assert banking_service.get_total_funds() == pytest.approx(expected)


def test_banking_service_notification_failure_side_effect(
    banking_service: BankingService,
    mock_notifier: Mock,
) -> None:
    """Тестування відмови зовнішнього сповіщувача через Mock side_effect."""
    mock_notifier.notify.side_effect = NotificationDeliveryError(
        "SMS шлюз недоступний через збій мережі"
    )

    with pytest.raises(NotificationDeliveryError) as exc_info:
        banking_service.deposit("UA10000001", 100.0)

    assert "SMS шлюз недоступний" in str(exc_info.value)
    mock_notifier.notify.assert_called_once()


@pytest.mark.asyncio
async def test_async_banking_gateway_authorized() -> None:
    """Тестування асинхронного шлюзу з використанням AsyncMock."""
    mock_client = Mock()
    mock_client.authorize = AsyncMock(
        return_value={"status": "AUTHORIZED", "code": 200}
    )

    gateway = AsyncBankingGateway(client=mock_client)
    status = await gateway.verify_transaction("UA10000001", 300.0)

    assert status == "AUTHORIZED"
    mock_client.authorize.assert_awaited_once_with("UA10000001", 300.0)


@pytest.mark.asyncio
async def test_banking_service_verified_transfer_success(
    in_memory_repo: InMemoryAccountRepository,
    mock_notifier: Mock,
) -> None:
    """Асинхронний сценарій успішного верифікованого переказу коштів."""
    mock_client = Mock()
    mock_client.authorize = AsyncMock(
        return_value={"status": "AUTHORIZED"}
    )
    gateway = AsyncBankingGateway(client=mock_client)

    service = BankingService(
        repository=in_memory_repo,
        notifier=mock_notifier,
        gateway=gateway,
    )

    result = await service.execute_verified_transfer("UA10000001", 500.0)
    assert result is True
    assert service.get_balance("UA10000001") == pytest.approx(1000.50)
    mock_client.authorize.assert_awaited_once_with("UA10000001", 500.0)
    mock_notifier.notify.assert_called_once()


@pytest.mark.asyncio
async def test_banking_service_verified_transfer_declined(
    in_memory_repo: InMemoryAccountRepository,
    mock_notifier: Mock,
) -> None:
    """При відхиленні шлюзом транзакція блокується, баланс не змінюється."""
    mock_client = Mock()
    mock_client.authorize = AsyncMock(
        return_value={"status": "DECLINED"}
    )
    gateway = AsyncBankingGateway(client=mock_client)

    service = BankingService(
        repository=in_memory_repo,
        notifier=mock_notifier,
        gateway=gateway,
    )

    result = await service.execute_verified_transfer("UA10000001", 500.0)
    assert result is False
    assert service.get_balance("UA10000001") == pytest.approx(1500.50)
    mock_client.authorize.assert_awaited_once_with("UA10000001", 500.0)
    mock_notifier.notify.assert_not_called()


@pytest.mark.asyncio
async def test_banking_service_verified_transfer_no_gateway(
    banking_service: BankingService,
) -> None:
    """Виклик верифікованого переказу без конфігурації шлюзу повертає False."""
    result = await banking_service.execute_verified_transfer(
        "UA10000001",
        200.0,
    )
    assert result is False
    assert banking_service.get_balance("UA10000001") == pytest.approx(1500.50)
