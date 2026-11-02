"""Головний модуль конвеєра імпорту та обробки банківських операцій."""

import argparse
import logging
from pathlib import Path
import sys

from .config import load_config
from .exceptions import ApplicationError
from .exporters import export_accounts_json
from .logging_config import setup_logging
from .services import (
    ImportStatistics,
    filter_by_balance,
    import_accounts,
)

logger = logging.getLogger("reliable_importer")


def run_pipeline(config_path: Path) -> ImportStatistics:
    """Виконання повного циклу імпорту, валідації, фільтрації та експорту."""
    config = load_config(config_path)
    setup_logging(config.logging)

    logger.info("Запуск банківського конвеєра з конфігурації: %s", config_path)
    logger.info("Вхідний файл: %s", config.input_path)
    logger.info("Вихідний файл: %s", config.output_path)

    stats = ImportStatistics()
    accounts_iter = import_accounts(
        config.input_path,
        skip_invalid=config.processing.skip_invalid,
        statistics=stats,
    )

    filtered_iter = filter_by_balance(
        accounts_iter,
        minimum_balance=config.processing.minimum_balance,
    )

    stats.exported = export_accounts_json(filtered_iter, config.output_path)

    logger.info(
        "Конвеєр завершено: всього=%d, валідних=%d, помилкових=%d, "
        "експортовано=%d",
        stats.total,
        stats.valid,
        stats.invalid,
        stats.exported,
    )
    return stats


def main() -> None:
    """Точка входу для командного рядка."""
    parser = argparse.ArgumentParser(
        description="Банківська система імпорту та обробки рахунків."
    )
    parser.add_argument(
        "-c",
        "--config",
        type=Path,
        default=Path("config.yaml"),
        help="Шлях до файлу конфігурації (за замовчуванням config.yaml)",
    )
    args = parser.parse_args()

    try:
        stats = run_pipeline(args.config)
        print(
            f"Успішно завершено. Оброблено: {stats.total}, "
            f"експортовано: {stats.exported}"
        )
    except ApplicationError as error:
        logger.error("Критична помилка виконання: %s", error)
        print(f"Помилка: {error}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
