"""Модульні тести завантаження та валідації конфігурації додатку."""

from pathlib import Path

import pytest

from reliable_importer.config import load_config, validate_config
from reliable_importer.exceptions import ConfigurationError
from reliable_importer.models import (
    AppConfig,
    LoggingConfig,
    ProcessingConfig,
)


def test_load_config_valid(sample_config_yaml: Path) -> None:
    """Перевірка коректного зчитування дійсного файлу конфігурації."""
    config = load_config(sample_config_yaml)
    assert isinstance(config, AppConfig)
    assert config.processing.minimum_balance == pytest.approx(100.0)
    assert config.processing.skip_invalid is True
    assert config.logging.level == "INFO"
    assert config.input_path.exists()


def test_load_config_file_not_found(tmp_path: Path) -> None:
    """Відсутність файлу конфігурації викликає ConfigurationError."""
    missing = tmp_path / "missing_config.yaml"
    with pytest.raises(ConfigurationError) as exc_info:
        load_config(missing)

    assert "не знайдено" in str(exc_info.value)
    assert isinstance(exc_info.value.__cause__, FileNotFoundError)


def test_load_config_invalid_yaml_syntax(tmp_path: Path) -> None:
    """Синтаксичні помилки в YAML викликають ConfigurationError."""
    bad_yaml = tmp_path / "bad_syntax.yaml"
    bad_yaml.write_text("input:\n  path: [unclosed_list", encoding="utf-8")

    with pytest.raises(ConfigurationError) as exc_info:
        load_config(bad_yaml)

    assert "Помилка синтаксису YAML" in str(exc_info.value)


def test_load_config_non_dict_root(tmp_path: Path) -> None:
    """Кореневий список замість словника викликає ConfigurationError."""
    list_yaml = tmp_path / "list_root.yaml"
    list_yaml.write_text("- item1\n- item2\n", encoding="utf-8")

    with pytest.raises(ConfigurationError) as exc_info:
        load_config(list_yaml)

    assert "має бути словником" in str(exc_info.value)


def test_load_config_missing_section(tmp_path: Path) -> None:
    """Відсутність обов'язкової секції викликає ConfigurationError."""
    broken_yaml = tmp_path / "incomplete.yaml"
    broken_yaml.write_text(
        "input:\n  path: data.csv\noutput:\n  path: out.json\n",
        encoding="utf-8",
    )

    with pytest.raises(ConfigurationError) as exc_info:
        load_config(broken_yaml)

    assert "Некоректна структура" in str(exc_info.value)


def test_validate_config_negative_minimum_balance(
    tmp_path: Path,
    sample_csv_file: Path,
) -> None:
    """Від'ємне значення minimum_balance відхиляється валідатором."""
    config = AppConfig(
        input_path=sample_csv_file,
        output_path=tmp_path / "out.json",
        processing=ProcessingConfig(minimum_balance=-50.0, skip_invalid=True),
        logging=LoggingConfig(level="INFO", path=tmp_path / "app.log"),
    )
    with pytest.raises(
        ConfigurationError,
        match="minimum_balance не може бути від'ємним",
    ):
        validate_config(config)


def test_validate_config_nonexistent_input_file(tmp_path: Path) -> None:
    """Відсутній вхідний CSV файл викликає ConfigurationError."""
    config = AppConfig(
        input_path=tmp_path / "non_existent.csv",
        output_path=tmp_path / "out.json",
        processing=ProcessingConfig(minimum_balance=100.0, skip_invalid=True),
        logging=LoggingConfig(level="INFO", path=tmp_path / "app.log"),
    )
    with pytest.raises(ConfigurationError, match="Вхідний файл не знайдено"):
        validate_config(config)


def test_validate_config_invalid_log_level(
    tmp_path: Path,
    sample_csv_file: Path,
) -> None:
    """Невідомий рівень журналювання викликає ConfigurationError."""
    config = AppConfig(
        input_path=sample_csv_file,
        output_path=tmp_path / "out.json",
        processing=ProcessingConfig(minimum_balance=100.0, skip_invalid=True),
        logging=LoggingConfig(
            level="INVALID_LEVEL",
            path=tmp_path / "app.log",
        ),
    )
    with pytest.raises(
        ConfigurationError,
        match="Некоректний рівень логування",
    ):
        validate_config(config)


def test_load_config_invalid_skip_invalid_type(
    tmp_path: Path,
    sample_csv_file: Path,
) -> None:
    """Небулеве значення skip_invalid викликає ConfigurationError."""
    cfg_file = tmp_path / "bad_type.yaml"
    content = (
        f"input:\n  path: {sample_csv_file.as_posix()}\n"
        f"output:\n  path: {tmp_path.as_posix()}/out.json\n"
        f"processing:\n  minimum_balance: 100.0\n  skip_invalid: 'not_bool'\n"
        f"logging:\n  level: INFO\n  path: {tmp_path.as_posix()}/log\n"
    )
    cfg_file.write_text(content, encoding="utf-8")

    with pytest.raises(ConfigurationError) as exc_info:
        load_config(cfg_file)

    assert "Некоректна структура" in str(exc_info.value)


def test_load_config_with_monkeypatch(
    tmp_path: Path,
    sample_config_yaml: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Перевірка ізоляції оточення за допомогою monkeypatch."""
    monkeypatch.setenv("BANK_APP_ENV", "TESTING")
    import os

    assert os.environ.get("BANK_APP_ENV") == "TESTING"

    config = load_config(sample_config_yaml)
    assert config.processing.skip_invalid is True
