"""Налаштування журналювання та маскування чутливих банківських даних."""

import logging
from logging.handlers import RotatingFileHandler

from .models import LoggingConfig


def mask_sensitive_account(account_number: str) -> str:
    """Маскування номера банківського рахунку для захисту персональних даних.

    Приклади:
    - 'UA10000001' -> 'UA10****0001'
    - '12345' -> '12***'
    - '' -> '***'
    """
    clean = account_number.strip()
    if len(clean) >= 8:
        return f"{clean[:4]}****{clean[-4:]}"
    if len(clean) >= 4:
        return f"{clean[:2]}***{clean[-2:]}"
    if clean:
        return f"{clean[:1]}***"
    return "***"


def setup_logging(config: LoggingConfig) -> None:
    """Конфігурація кореневого логера з ротацією та форматуванням."""
    config.path.parent.mkdir(parents=True, exist_ok=True)
    level = getattr(logging, config.level.upper(), logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    file_handler = RotatingFileHandler(
        config.path,
        maxBytes=1_048_576,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()
    root.addHandler(file_handler)
    root.addHandler(console_handler)
