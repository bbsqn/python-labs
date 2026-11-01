"""Модуль налаштування журналювання із захистом конфіденційних даних."""

import logging
from pathlib import Path


def mask_sensitive_account(account_number: str) -> str:
    """Маскує номер банківського рахунку (наприклад UA12****7890)."""
    clean = account_number.strip()
    if len(clean) <= 6:
        return "***"
    prefix = clean[:4]
    suffix = clean[-4:]
    return f"{prefix}****{suffix}"


def configure_logging(level: str, path: Path) -> None:
    """Конфігурує журналювання у файл та консоль з форматуванням."""
    path.parent.mkdir(parents=True, exist_ok=True)
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    file_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )
    console_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s"
    )

    file_handler = logging.FileHandler(path, encoding="utf-8")
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(file_formatter)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(console_formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    root_logger.handlers.clear()
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
