"""Модуль сервісів імпорту, обробки та фільтрації даних."""

from collections.abc import Iterable, Iterator
from dataclasses import dataclass
import logging
from pathlib import Path

from .exceptions import RecordValidationError
from .logging_config import mask_sensitive_account
from .models import BankAccountRecord
from .readers import read_csv_rows
from .validators import parse_account

logger = logging.getLogger(__name__)


@dataclass
class ImportStatistics:
    """Лічильник статистики обробки записів."""

    total: int = 0
    valid: int = 0
    invalid: int = 0
    exported: int = 0


def import_accounts(
    path: Path,
    *,
    skip_invalid: bool,
    statistics: ImportStatistics,
) -> Iterator[BankAccountRecord]:
    """Потоковий імпорт банківських записів з підтримкою Strict / Tolerant:

    - Strict mode (skip_invalid=False): перша помилка перериває процес.
    - Tolerant mode (skip_invalid=True): некоректні записи логуються та
      пропускаються.
    """
    for line_number, row in read_csv_rows(path):
        statistics.total += 1
        try:
            account = parse_account(row, line_number=line_number)
        except RecordValidationError as error:
            statistics.invalid += 1
            acc_raw = row.get("account_number", "")
            masked = mask_sensitive_account(acc_raw)
            logger.warning(
                "Невалідний запис у рядку %s (рахунок %s, поле %s): %s",
                error.line_number,
                masked,
                error.field,
                error,
            )
            if skip_invalid:
                continue
            raise

        statistics.valid += 1
        yield account


def filter_by_balance(
    accounts: Iterable[BankAccountRecord],
    minimum_balance: float,
) -> Iterator[BankAccountRecord]:
    """Потокова фільтрація рахунків за мінімальним балансом."""
    for account in accounts:
        if account.balance >= minimum_balance:
            yield account
