"""Інтеграційні тести повного життєвого циклу банківських операцій (End-to-End Account Flow)."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest

from bank_system.exceptions import InsufficientFundsError
from bank_system.exporters import export_accounts_json
from bank_system.models import Account
from bank_system.protocols import AsyncBankingClient, Notifier
from bank_system.repositories import FakeAccountRepository
from bank_system.services import AsyncBankingGateway, BankingService


@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_account_operation_flow(tmp_path: Path) -> None:
    """Повний інтеграційний сценарій:

    1. Реєстрація рахунків у репозиторії.
    2. Асинхронна авторизація великої транзакції через платіжний шлюз.
    3. Виконання поповнення, зняття та міжбанківського переказу.
    4. Аудит взаємодії зі сповіщувачем.
    5. Перевірка цілісності фінансового балансу системи.
    6. Експорт підсумкового стану рахунків у JSON.
    """
    repository = FakeAccountRepository()
    notifier = Mock(spec=Notifier)
    async_client = AsyncMock(spec=AsyncBankingClient)
    async_client.authorize.return_value = {"status": "APPROVED"}

    gateway = AsyncBankingGateway(client=async_client)
    service = BankingService(repository=repository, notifier=notifier)

    # 1. Реєстрація рахунків
    acc_alice = Account("UA00000001", "Аліса Кравченко", 5000.0)
    acc_bob = Account("UA00000002", "Богдан Мельник", 1000.0)
    repository.add(acc_alice)
    repository.add(acc_bob)

    # 2. Асинхронна перевірка у зовнішньому шлюзі перед операцією
    auth_status = await gateway.verify_transaction(acc_alice.account_number, 1500.0)
    assert auth_status == "APPROVED"
    async_client.authorize.assert_awaited_once_with("UA00000001", 1500.0)

    # 3. Виконання операцій
    service.process_deposit("UA00000002", 500.0, "bob@example.com")
    service.transfer("UA00000001", "UA00000002", 1500.0, "alice@example.com")

    # 4. Перевірка сповіщень
    assert notifier.send.call_count == 2

    # 5. Перевірка залишків та сумарних коштів
    assert acc_alice.balance == pytest.approx(3500.0)
    assert acc_bob.balance == pytest.approx(3000.0)
    assert repository.total_funds() == pytest.approx(6500.0)

    # 6. Експорт підсумкового стану рахунків
    out_json = tmp_path / "system_state.json"
    export_accounts_json(repository.list_all(), out_json)

    assert out_json.exists()
    saved = json.loads(out_json.read_text(encoding="utf-8"))
    assert len(saved) == 2


@pytest.mark.integration
def test_atomic_transfer_failure_preserves_balances(
    populated_repository: FakeAccountRepository,
) -> None:
    """Інтеграційний тест відмови: при нестачі коштів залишки обох рахунків лишаються незмінними."""
    notifier = Mock(spec=Notifier)
    service = BankingService(repository=populated_repository, notifier=notifier)

    initial_src_balance = populated_repository.get("UA00000001").balance  # type: ignore[union-attr]
    initial_tgt_balance = populated_repository.get("UA00000002").balance  # type: ignore[union-attr]

    # Спроба зняти більше, ніж є на рахунку UA00000001 (1000.0 грн)
    with pytest.raises(InsufficientFundsError):
        service.transfer("UA00000001", "UA00000002", 50000.0, "sender@example.com")

    # Залишки не змінилися
    acc1 = populated_repository.get("UA00000001")
    acc2 = populated_repository.get("UA00000002")
    assert acc1 is not None and acc1.balance == pytest.approx(initial_src_balance)
    assert acc2 is not None and acc2.balance == pytest.approx(initial_tgt_balance)
    notifier.send.assert_not_called()
