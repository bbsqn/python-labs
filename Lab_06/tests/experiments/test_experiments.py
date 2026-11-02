"""Лабораторні експерименти (Розділи 84-90 методичних вказівок).

Експеримент 1: Слабкі тести проти сильних (execution != verification).
Експеримент 2: Тестове покриття без тверджень проти перевірки тверджень.
Експеримент 3: Аналіз покриття розгалужень (Branch Coverage).
Експеримент 4: Порівняння Mock-об'єктів та Fake-репозиторію.
Експеримент 5: Flaky-тести (випадковість/час) проти детермінованих тестів.
Експеримент 6: Ізоляція файлової системи через tmp_path проти спільного шляху.
Експеримент 7: Тестування сценаріїв відмови через mock.side_effect.
"""

import datetime
from pathlib import Path
import random
from unittest.mock import Mock

import pytest

from reliable_importer.exceptions import (
    InsufficientFundsError,
    NotificationDeliveryError,
)
from reliable_importer.models import BankAccount
from reliable_importer.services import (
    AccountRepository,
    BankingService,
    InMemoryAccountRepository,
    Notifier,
)


def test_experiment_1_weak_test_misses_mutation() -> None:
    """Слабкий тест: лише виконання без верифікації стану."""
    repo = InMemoryAccountRepository()
    repo.add(BankAccount("UA_WEAK", "Клієнт", 1000.0))
    notifier = Mock(spec=Notifier)
    service = BankingService(repo, notifier)

    service.deposit("UA_WEAK", 500.0)
    assert True


def test_experiment_1_strong_test_catches_mutation() -> None:
    """Сильний тест: сувора перевірка стану, значень та викликів."""
    repo = InMemoryAccountRepository()
    repo.add(BankAccount("UA_STRONG", "Клієнт", 1000.0))
    notifier = Mock(spec=Notifier)
    service = BankingService(repo, notifier)

    new_balance = service.deposit("UA_STRONG", 500.0)

    assert new_balance == pytest.approx(1500.0)
    acc = repo.get("UA_STRONG")
    assert acc is not None
    assert acc.balance == pytest.approx(1500.0)
    notifier.notify.assert_called_once_with(
        "UA_STRONG",
        "Поповнення 500.00 грн. Баланс: 1500.00 грн.",
    )


def buggy_withdraw(account: BankAccount, amount: float) -> float:
    """Мутація коду: зняття без перевірки доступного балансу (овердрафт)."""
    account.balance = round(account.balance - amount, 2)
    return account.balance


def test_experiment_2_coverage_without_assertions() -> None:
    """Тест забезпечує 100% покриття рядків функції, але пропускає баг."""
    acc = BankAccount("UA_EXP2", "Клієнт", 100.0)
    buggy_withdraw(acc, 500.0)


def test_experiment_2_assertions_detect_fault() -> None:
    """Тест із твердженням фіксує порушення контракту цілісності."""
    acc = BankAccount("UA_EXP2", "Клієнт", 100.0)
    with pytest.raises(InsufficientFundsError):
        acc.withdraw(500.0)


@pytest.mark.parametrize(
    ("balance", "expected_tier"),
    [
        (500.0, "Standard"),
        (2500.0, "Silver"),
        (10000.0, "Gold"),
        (50000.0, "Platinum"),
    ],
)
def test_experiment_3_branch_coverage_all_paths(
    balance: float,
    expected_tier: str,
) -> None:
    """Повне покриття всіх альтернативних гілок оператора розгалуження."""
    acc = BankAccount("UA_BRANCH", "Клієнт", balance)
    assert acc.classify_tier() == expected_tier


def test_experiment_4_mock_interaction_verification() -> None:
    """Mock перевіряє факт та параметри виклику (протокол взаємодії)."""
    mock_repo = Mock(spec=AccountRepository)
    test_acc = BankAccount("UA_MOCK", "Клієнт", 100.0)
    mock_repo.get.return_value = test_acc
    mock_notifier = Mock(spec=Notifier)

    service = BankingService(mock_repo, mock_notifier)
    service.deposit("UA_MOCK", 50.0)

    mock_repo.get.assert_called_once_with("UA_MOCK")
    mock_notifier.notify.assert_called_once()


def test_experiment_4_fake_state_verification() -> None:
    """Fake перевіряє зміну внутрішнього стану та контракт збереження."""
    fake_repo = InMemoryAccountRepository()
    fake_repo.add(BankAccount("UA_FAKE", "Клієнт", 100.0))
    mock_notifier = Mock(spec=Notifier)

    service = BankingService(fake_repo, mock_notifier)
    service.deposit("UA_FAKE", 50.0)

    updated = fake_repo.get("UA_FAKE")
    assert updated is not None
    assert updated.balance == pytest.approx(150.0)
    assert fake_repo.total_funds() == pytest.approx(150.0)


def is_night_audit_deterministic(current_time: datetime.datetime) -> bool:
    """Детермінована функція через явне впровадження залежності (DI)."""
    return current_time.hour >= 23 or current_time.hour < 5


def test_experiment_5_flaky_test_concept() -> None:
    """Ілюстрація: зафіксоване зерно усуває випадковість."""
    random.seed(42)
    val = random.randint(1, 100)
    assert val == 82


def test_experiment_5_deterministic_with_fixed_clock() -> None:
    """Фіксований час гарантує 100% повторюваність результатів тесту."""
    night_time = datetime.datetime(2026, 11, 2, 23, 30, 0)
    day_time = datetime.datetime(2026, 11, 2, 14, 0, 0)

    assert is_night_audit_deterministic(night_time) is True
    assert is_night_audit_deterministic(day_time) is False


def test_experiment_6_isolated_filesystem(tmp_path: Path) -> None:
    """tmp_path створює ізольоване середовище без конфліктів файлів."""
    file_a = tmp_path / "accounts_batch_a.csv"
    file_a.write_text("UA01,Остап,100\n", encoding="utf-8")
    assert file_a.exists()
    assert file_a.read_text(encoding="utf-8") == "UA01,Остап,100\n"


def test_experiment_6_isolated_filesystem_independent(
    tmp_path: Path,
) -> None:
    """Кожен тестовий виклик отримує повністю порожній каталог."""
    assert list(tmp_path.iterdir()) == []


def test_experiment_7_side_effect_simulated_outage(
    banking_service: BankingService,
    mock_notifier: Mock,
) -> None:
    """side_effect симулює аварійну відмову зв'язку з клієнтським шлюзом."""
    mock_notifier.notify.side_effect = NotificationDeliveryError(
        "HTTP 503 Service Unavailable"
    )

    with pytest.raises(NotificationDeliveryError) as exc_info:
        banking_service.deposit("UA10000001", 100.0)

    assert "HTTP 503" in str(exc_info.value)
    mock_notifier.notify.assert_called_once()
