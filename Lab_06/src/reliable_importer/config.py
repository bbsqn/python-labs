"""Завантаження та валідація YAML конфігурації (Fail-Fast принцип)."""

from pathlib import Path
import yaml

from .exceptions import ConfigurationError
from .models import AppConfig, LoggingConfig, ProcessingConfig

VALID_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


def validate_config(config: AppConfig) -> None:
    """Валідація параметрів конфігурації за принципом Fail-Fast."""
    if config.processing.minimum_balance < 0:
        raise ConfigurationError(
            "Параметр minimum_balance не може бути від'ємним."
        )

    if not config.input_path.exists():
        raise ConfigurationError(
            f"Вхідний файл не знайдено: {config.input_path}"
        )

    if config.logging.level.upper() not in VALID_LOG_LEVELS:
        raise ConfigurationError(
            f"Некоректний рівень логування: {config.logging.level}"
        )


def load_config(path: Path) -> AppConfig:
    """Зчитування та валідація конфігурації з файлу YAML."""
    try:
        with path.open("r", encoding="utf-8") as file:
            raw = yaml.safe_load(file)
    except FileNotFoundError as error:
        raise ConfigurationError(
            f"Конфігураційний файл не знайдено: {path}"
        ) from error
    except yaml.YAMLError as error:
        raise ConfigurationError(
            f"Помилка синтаксису YAML у файлі {path}: {error}"
        ) from error

    if not isinstance(raw, dict):
        raise ConfigurationError(
            "Кореневий елемент конфігурації має бути словником."
        )

    try:
        input_raw = raw["input"]["path"]
        output_raw = raw["output"]["path"]
        proc_raw = raw["processing"]
        log_raw = raw["logging"]

        skip_inv = proc_raw["skip_invalid"]
        if not isinstance(skip_inv, bool):
            raise TypeError("skip_invalid має бути булевим значенням.")

        config = AppConfig(
            input_path=Path(input_raw),
            output_path=Path(output_raw),
            processing=ProcessingConfig(
                minimum_balance=float(proc_raw["minimum_balance"]),
                skip_invalid=skip_inv,
            ),
            logging=LoggingConfig(
                level=str(log_raw["level"]).upper(),
                path=Path(log_raw["path"]),
            ),
        )
    except (KeyError, TypeError, ValueError) as error:
        raise ConfigurationError(
            f"Некоректна структура конфігураційного файлу: {error}"
        ) from error

    validate_config(config)
    return config
