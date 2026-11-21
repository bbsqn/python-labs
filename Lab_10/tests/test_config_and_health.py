"""Тести production-конфігурації, журналювання та healthcheck endpoint."""

from __future__ import annotations

import logging

import pytest
from fastapi.testclient import TestClient

from bank_account_service.config import Settings, configure_logging, get_settings


def test_health_endpoint(client: TestClient) -> None:
    """Перевірка GET /health (200 OK, status та environment)."""
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["environment"] in {"development", "test", "production"}


def test_default_settings() -> None:
    """Перевірка значень конфігурації за замовчуванням."""
    settings = Settings()
    assert settings.app_name == "Bank Account Service"
    assert settings.environment in {"development", "test", "production"}
    assert settings.database_url.startswith("sqlite")
    assert settings.log_level == "INFO"


def test_environment_variable_override(monkeypatch: pytest.MonkeyPatch) -> None:
    """Перевірка передавання параметрів через environment variables без змін коду."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./custom_prod.db")
    get_settings.cache_clear()
    try:
        loaded = get_settings()
        assert loaded.environment == "production"
        assert loaded.log_level == "DEBUG"
        assert loaded.database_url == "sqlite:///./custom_prod.db"
        logger = configure_logging(loaded.log_level)
        assert logger.getEffectiveLevel() == logging.DEBUG
    finally:
        get_settings.cache_clear()


def test_app_env_alias_supported(monkeypatch: pytest.MonkeyPatch) -> None:
    """Перевірка підтримки змінної середовища APP_ENV як аліаса ENVIRONMENT."""
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    monkeypatch.setenv("APP_ENV", "production")
    get_settings.cache_clear()
    try:
        settings = get_settings()
        assert settings.environment == "production"
    finally:
        get_settings.cache_clear()
