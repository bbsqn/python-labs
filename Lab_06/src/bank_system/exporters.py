"""Імпорт рахунків з CSV-файлів та експорт у формат JSON."""

import csv
import json
from pathlib import Path

from .exceptions import AccountValidationError, DataExportError, DataImportError
from .models import Account


def import_accounts_csv(path: Path) -> list[Account]:
    """Зчитати та валідувати банківські рахунки з файлу формату CSV."""
    if not path.exists():
        raise DataImportError(f"Файл імпорту не існує: {path}")

    accounts: list[Account] = []
    try:
        with open(path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None:
                raise DataImportError("Порожній або пошкоджений CSV-файл.")

            required_fields = {"account_number", "client", "balance"}
            if not required_fields.issubset(set(reader.fieldnames)):
                raise DataImportError(
                    f"CSV-файл не містить обов'язкових колонок: {required_fields}"
                )

            for line_no, row in enumerate(reader, start=2):
                acc_num = (row.get("account_number") or "").strip()
                client = (row.get("client") or "").strip()
                balance_raw = (row.get("balance") or "").strip()
                currency = (row.get("currency") or "UAH").strip()

                if not acc_num or not client or not balance_raw:
                    raise DataImportError(
                        f"Рядок {line_no} містить порожні обов'язкові поля."
                    )

                try:
                    balance = float(balance_raw)
                except ValueError as err:
                    raise DataImportError(
                        f"Рядок {line_no}: некоректне значення балансу '{balance_raw}'."
                    ) from err

                try:
                    account = Account(
                        account_number=acc_num,
                        client=client,
                        balance=balance,
                        currency=currency,
                    )
                except AccountValidationError as err:
                    raise DataImportError(
                        f"Рядок {line_no}: помилка валідації рахунку: {err}"
                    ) from err

                accounts.append(account)

    except OSError as err:
        raise DataImportError(f"Помилка доступу до файлу: {err}") from err

    return accounts


def export_accounts_json(accounts: list[Account], path: Path) -> None:
    """Експортувати список рахунків у структурований JSON-файл."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        data = [acc.to_dict() for acc in accounts]
        serialized = json.dumps(data, ensure_ascii=False, indent=2)
        path.write_text(serialized, encoding="utf-8")
    except (OSError, TypeError) as err:
        raise DataExportError(f"Помилка експорту в JSON: {err}") from err

