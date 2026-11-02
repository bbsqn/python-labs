"""Атомарний експорт результатів обробки банківських рахунків у JSON."""

from collections.abc import Generator, Iterable
from contextlib import contextmanager
import json
import os
from pathlib import Path

from .exceptions import DataError, DataExportError
from .models import BankAccountRecord


@contextmanager
def atomic_write(destination: Path) -> Generator[Path, None, None]:
    """Контекстний менеджер атомарного запису файлів на диск.

    Створює тимчасовий файл .tmp у тому ж каталозі, а після успішного
    запису виконує атомарну заміну (os.replace).
    У разі збою тимчасовий файл видаляється.
    """
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp_path = destination.with_suffix(f"{destination.suffix}.tmp")

    try:
        yield temp_path
        os.replace(temp_path, destination)
    except Exception as error:
        if temp_path.exists():
            temp_path.unlink()
        raise DataExportError(
            f"Аварія атомарного збереження у файл {destination}: {error}"
        ) from error


def export_accounts_json(
    records: Iterable[BankAccountRecord],
    destination: Path,
) -> int:
    """Експорт послідовності банківських записів у валідний JSON файл."""
    count = 0
    records_list = []

    try:
        for record in records:
            records_list.append(record.to_dict())
            count += 1

        with atomic_write(destination) as temp_target:
            with temp_target.open("w", encoding="utf-8") as file:
                json.dump(records_list, file, ensure_ascii=False, indent=2)
    except DataError:
        raise
    except Exception as error:
        raise DataExportError(
            f"Помилка серіалізації або запису в {destination}: {error}"
        ) from error

    return count
