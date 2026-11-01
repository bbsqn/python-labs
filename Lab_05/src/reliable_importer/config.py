"""Модуль завантаження та валідації YAML конфігурації."""

from pathlib import Path
import yaml

from .exceptions import ConfigurationError
from .models import AppConfig, LoggingConfig, ProcessingConfig

VALID_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


def validate_config(config: AppConfig) -> None:
    """Перевіряє коректність параметрів конфігурації (Fail-Fast)."""
    if config.processing.minimum_balance < 0:
        raise ConfigurationError(
            "Параметр minimum_balance не може бути від'ємним"
        )

    if not config.input_path.exists():
        raise ConfigurationError(
            f"Вхідний файл не знайдено: {config.input_path}"
        )

    if config.logging.level.upper() not in VALID_LOG_LEVELS:
        raise ConfigurationError(
            f"Невідомий рівень логування: {config.logging.level}"
        )


def load_config(path: Path) -> AppConfig:
    """Завантажує та валідує конфігурацію з YAML-файлу."""
    try:
        with path.open("r", encoding="utf-8") as file:
            raw = yaml.safe_load(file)
    except FileNotFoundError as error:
        raise ConfigurationError(
            f"Файл конфігурації не знайдено: {path}"
        ) from error
    except yaml.YAMLError as error:
        raise ConfigurationError(
            "Некоректний синтаксис YAML конфігурації"
        ) from error

    if not isinstance(raw, dict):
        raise ConfigurationError(
            "Конфігураційний файл повинен містити словник"
        )

    try:
        input_raw = raw["input"]["path"]
        output_raw = raw["output"]["path"]
        proc_raw = raw["processing"]
        log_raw = raw["logging"]

        config = AppConfig(
            input_path=Path(input_raw),
            output_path=Path(output_raw),
            processing=ProcessingConfig(
                minimum_balance=float(proc_raw["minimum_balance"]),
                skip_invalid=bool(proc_raw["skip_invalid"]),
            ),
            logging=LoggingConfig(
                level=str(log_raw["level"]),
                path=Path(log_raw["path"]),
            ),
        )
    except (KeyError, TypeError, ValueError) as error:
        raise ConfigurationError(
            "Структура конфігураційного файлу є невалідною"
        ) from error

    validate_config(config)
    return config
