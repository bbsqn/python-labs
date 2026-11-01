"""Головна точка входу додатку імпорту та експорту даних (Lab 5)."""

# flake8: noqa: E402
from pathlib import Path
import sys

SRC_DIR = str(Path(__file__).resolve().parent.parent)
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

import logging

from reliable_importer.config import load_config
from reliable_importer.exceptions import ApplicationError
from reliable_importer.exporters import export_accounts_json
from reliable_importer.logging_config import configure_logging
from reliable_importer.services import (
    ImportStatistics,
    filter_by_balance,
    import_accounts,
)
from reliable_importer.utils import logged_operation

logger = logging.getLogger(__name__)


def main() -> None:
    """Головний сценарій виконання програми."""
    config_file = Path("config.yaml")
    if not config_file.exists():
        config_file = Path(__file__).resolve().parent.parent.parent / "config.yaml"

    try:
        config = load_config(config_file)
        configure_logging(config.logging.level, config.logging.path)

        statistics = ImportStatistics()

        with logged_operation("Імпорт та експорт банківських рахунків"):
            accounts_stream = import_accounts(
                config.input_path,
                skip_invalid=config.processing.skip_invalid,
                statistics=statistics,
            )

            filtered_stream = filter_by_balance(
                accounts_stream,
                config.processing.minimum_balance,
            )

            exported_count = export_accounts_json(
                filtered_stream,
                config.output_path,
            )
            statistics.exported = exported_count

        logger.info(
            "Підсумок обробки: Всього=%s, Валідних=%s, Невалідних=%s, "
            "Експортовано=%s",
            statistics.total,
            statistics.valid,
            statistics.invalid,
            statistics.exported,
        )
        print("\n" + "=" * 65)
        print("Обробку даних завершено успішно.")
        print(
            f"Всього: {statistics.total} | Валідних: {statistics.valid} | "
            f"Невалідних: {statistics.invalid} | Експортовано: {statistics.exported}"
        )
        print(f"Результат збережено у: {config.output_path}")
        print("=" * 65)

    except ApplicationError as error:
        logger.error("Критична помилка додатку: %s", error)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
