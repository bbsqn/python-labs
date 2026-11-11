"""Модульні тести бізнес-сервісів, макетування (Mock, AsyncMock) та ізоляції залежностей."""

from unittest.mock import AsyncMock, Mock

import pytest

from bank_system.exceptions import (
    AccountNotFoundError,
    NotificationError,
    PaymentGatewayError,
)
from bank_system.protocols import Notifier
from bank_system.repositories import FakeAccountRepository
from bank_system.services import AsyncBankingGateway, BankingService


def test_process_deposit_with_mock_notifier(
    populated_repository: FakeAccountRepository,
    mock_notifier: Mock,
) -> None:
    """Перевірка поповнення рахунку через сервіс та підтвердження виклику Mock-сповіщувача."""
    service = BankingService(repository=populated_repository, notifier=mock_notifier)

    new_balance = service.process_deposit(
        account_number="UA00000001",
        amount=500.0,
        recipient="ostap@example.com",
    )

    assert new_balance == pytest.approx(1500.0)
    mock_notifier.send.assert_called_once_with(
        "ostap@example.com",
        "Поповнення рахунку UA00000001 на суму 500.00 грн успішне. Баланс: 1500.00 грн.",
    )


def test_process_withdrawal_with_mock_notifier(
    populated_repository: FakeAccountRepository,
    mock_notifier: Mock,
) -> None:
    """Перевірка зняття коштів через сервіс та взаємодії зі сповіщувачем."""
    service = BankingService(repository=populated_repository, notifier=mock_notifier)

    new_balance = service.process_withdrawal(
        account_number="UA00000002",
        amount=1000.0,
        recipient="olena@example.com",
    )

    assert new_balance == pytest.approx(1500.0)
    mock_notifier.send.assert_called_once_with(
        "olena@example.com",
        "Зняття з рахунку UA00000002 на суму 1000.00 грн успішне. Баланс: 1500.00 грн.",
    )


def test_service_account_not_found_raises(
    fake_repository: FakeAccountRepository,
    mock_notifier: Mock,
) -> None:
    """Перевірка виникнення винятку при спробі операції над неіснуючим рахунком."""
    service = BankingService(repository=fake_repository, notifier=mock_notifier)

    with pytest.raises(AccountNotFoundError, match="Рахунок UA99999999 не знайдено"):
        service.process_deposit("UA99999999", 100.0, "user@example.com")

    mock_notifier.send.assert_not_called()


def test_notifier_failure_side_effect(
    populated_repository: FakeAccountRepository,
) -> None:
    """Перевірка обробки збою сповіщувача за допомогою механізму side_effect."""
    failing_notifier = Mock(spec=Notifier)
    failing_notifier.send.side_effect = NotificationError("Помилка доставки SMS")

    service = BankingService(repository=populated_repository, notifier=failing_notifier)

    with pytest.raises(NotificationError, match="Помилка доставки SMS"):
        service.process_deposit(
            account_number="UA00000001",
            amount=200.0,
            recipient="test@example.com",
        )

    failing_notifier.send.assert_called_once()


def test_transfer_between_accounts_success(
    populated_repository: FakeAccountRepository,
    mock_notifier: Mock,
) -> None:
    """Перевірка операції міжбанківського переказу між двома рахунками."""
    service = BankingService(repository=populated_repository, notifier=mock_notifier)

    src_bal, tgt_bal = service.transfer(
        from_account_number="UA00000001",
        to_account_number="UA00000002",
        amount=300.0,
        sender_recipient="sender@example.com",
    )

    assert src_bal == pytest.approx(700.0)
    assert tgt_bal == pytest.approx(2800.0)
    mock_notifier.send.assert_called_once_with(
        "sender@example.com",
        "Переказ 300.00 грн на рахунок UA00000002 виконано успішно.",
    )


def test_transfer_source_account_not_found_raises(
    populated_repository: FakeAccountRepository,
    mock_notifier: Mock,
) -> None:
    """Перевірка винятку при відсутності рахунку відправника при переказі."""
    service = BankingService(repository=populated_repository, notifier=mock_notifier)

    with pytest.raises(AccountNotFoundError, match="Рахунок відправника"):
        service.transfer("NON_EXISTENT", "UA00000001", 100.0, "test@example.com")

    mock_notifier.send.assert_not_called()


def test_transfer_target_account_not_found_raises(
    populated_repository: FakeAccountRepository,
    mock_notifier: Mock,
) -> None:
    """Перевірка винятку при відсутності рахунку одержувача при переказі."""
    service = BankingService(repository=populated_repository, notifier=mock_notifier)

    with pytest.raises(AccountNotFoundError, match="Рахунок одержувача"):
        service.transfer("UA00000001", "NON_EXISTENT", 100.0, "test@example.com")

    mock_notifier.send.assert_not_called()


def test_repository_total_funds_and_queries(
    populated_repository: FakeAccountRepository,
) -> None:
    """Перевірка агрегації загальної суми коштів та розміру репозиторію."""
    assert len(populated_repository) == 3
    assert "UA00000001" in populated_repository
    assert "UA99999999" not in populated_repository
    assert populated_repository.total_funds() == pytest.approx(4000.0)


def test_get_account_balance_success(
    populated_repository: FakeAccountRepository,
    mock_notifier: Mock,
) -> None:
    """Перевірка отримання поточного залишку коштів на рахунку."""
    service = BankingService(repository=populated_repository, notifier=mock_notifier)
    balance = service.get_account_balance("UA00000001")
    assert balance == pytest.approx(1000.0)
    assert service.calculate_total_funds() == pytest.approx(4000.0)


@pytest.mark.asyncio
async def test_async_banking_gateway_success(mock_async_client: AsyncMock) -> None:
    """Перевірка успішної асинхронної авторизації через AsyncMock."""
    gateway = AsyncBankingGateway(client=mock_async_client)

    status = await gateway.verify_transaction("UA00000001", 500.0)

    assert status == "APPROVED"
    mock_async_client.authorize.assert_awaited_once_with("UA00000001", 500.0)


@pytest.mark.asyncio
async def test_async_banking_gateway_rejection_raises(mock_async_client: AsyncMock) -> None:
    """Перевірка винятку при відхиленні транзакції зовнішнім шлюзом."""
    mock_async_client.authorize.return_value = {"status": "DECLINED", "reason": "Risk"}
    gateway = AsyncBankingGateway(client=mock_async_client)

    with pytest.raises(PaymentGatewayError, match="відхилив транзакцію: DECLINED"):
        await gateway.verify_transaction("UA00000001", 50000.0)

    mock_async_client.authorize.assert_awaited_once_with("UA00000001", 50000.0)


@pytest.mark.asyncio
async def test_async_banking_gateway_network_error_side_effect(
    mock_async_client: AsyncMock,
) -> None:
    """Перевірка збою мережевого з'єднання в асинхронному шлюзі через side_effect."""
    mock_async_client.authorize.side_effect = ConnectionError("Connection reset by peer")
    gateway = AsyncBankingGateway(client=mock_async_client)

    with pytest.raises(ConnectionError, match="Connection reset by peer"):
        await gateway.verify_transaction("UA00000001", 100.0)
