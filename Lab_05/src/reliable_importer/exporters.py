"""Модуль атомарного експорту у JSON та звітів про помилки."""

from collections.abc import Iterable
import json
from pathlib import Path

from .exceptions import DataExportError
from .models import BankAccountRecord


def export_accounts_json(
    accounts: Iterable[BankAccountRecord],
    path: Path,
) -> int:
    """Атомарно записує потік рахунків у вихідний JSON масив:

    - Створює тимчасовий файл .tmp
    - Здійснює потоковий запис масиву
    - Атомарно замінює цільовий файл
    - У разі помилки видаляє тимчасовий файл та зберігає цільовий цілим
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    count = 0

    try:
        with temporary.open("w", encoding="utf-8") as file:
            file.write("[\n")
            first = True
            for account in accounts:
                if not first:
                    file.write(",\n")
                payload_str = json.dumps(
                    account.to_dict(),
                    ensure_ascii=False,
                    indent=2,
                )
                file.write(payload_str)
                first = False
                count += 1
            file.write("\n]\n")

        temporary.replace(path)
    except Exception as error:
        temporary.unlink(missing_ok=True)
        raise DataExportError(
            f"Не вдалося виконати атомарний експорт у {path}"
        ) from error

    return count
