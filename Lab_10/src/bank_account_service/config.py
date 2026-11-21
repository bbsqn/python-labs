"""Production-конфігурація застосунку через Pydantic BaseSettings та змінні середовища."""

from __future__ import annotations

import logging
from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Параметри застосунку, які завантажуються зі змінних середовища або .env."""

    app_name: str = "Bank Account Service"
    environment: str = Field(
        default="development",
        validation_alias=AliasChoices("ENVIRONMENT", "APP_ENV"),
    )
    database_url: str = "sqlite:///./bank_account_service.db"
    log_level: str = "INFO"
    api_key: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )


@lru_cache
def get_settings() -> Settings:
    """Повернути кешований екземпляр налаштувань застосунку."""
    return Settings()


def configure_logging(log_level: str | None = None) -> logging.Logger:
    """Налаштувати структуроване журналювання відповідно до рівня LOG_LEVEL."""
    resolved_level_name = (log_level or get_settings().log_level).upper()
    numeric_level = getattr(logging, resolved_level_name, logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    logging.getLogger().setLevel(numeric_level)
    return logging.getLogger("bank_account_service")
