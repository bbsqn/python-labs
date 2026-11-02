"""Інтеграційні тести повного життєвого циклу банківського додатку."""

import json
from pathlib import Path
import sys

import pytest

from reliable_importer.exceptions import RecordValidationError
from reliable_importer.main import main, run_pipeline


def test_application_flow_end_to_end(
    sample_config_yaml: Path,
    tmp_path: Path,
) -> None:
    """Повний наскрізний запуск конвеєра з перевіркою файлів та логів."""
    stats = run_pipeline(sample_config_yaml)

    assert stats.total == 3
    assert stats.valid == 3
    assert stats.invalid == 0
    assert stats.exported == 3

    out_file = tmp_path / "output" / "accounts.json"
    assert out_file.exists()

    with out_file.open("r", encoding="utf-8") as file:
        exported_data = json.load(file)

    assert len(exported_data) == 3
    assert exported_data[0]["account_number"] == "UA10000001"
    assert exported_data[0]["new_balance"] == pytest.approx(1700.50)

    log_file = tmp_path / "logs" / "test.log"
    assert log_file.exists()
    log_content = log_file.read_text(encoding="utf-8")
    assert "Запуск банківського конвеєра" in log_content
    assert "Конвеєр завершено" in log_content


def test_application_flow_tolerant_mode(
    malformed_csv_file: Path,
    tmp_path: Path,
) -> None:
    """Наскрізний запуск у режимі відновлення після помилок валідації."""
    cfg_file = tmp_path / "tolerant_config.yaml"
    out_file = tmp_path / "tolerant_out.json"
    log_file = tmp_path / "tolerant.log"

    cfg_content = (
        f"input:\n  path: {malformed_csv_file.as_posix()}\n"
        f"output:\n  path: {out_file.as_posix()}\n"
        f"processing:\n  minimum_balance: 50.0\n  skip_invalid: true\n"
        f"logging:\n  level: INFO\n  path: {log_file.as_posix()}\n"
    )
    cfg_file.write_text(cfg_content, encoding="utf-8")

    stats = run_pipeline(cfg_file)

    assert stats.total == 4
    assert stats.valid == 2
    assert stats.invalid == 2
    assert stats.exported == 2

    assert out_file.exists()
    with out_file.open("r", encoding="utf-8") as file:
        data = json.load(file)
    assert len(data) == 2

    assert log_file.exists()
    log_content = log_file.read_text(encoding="utf-8")
    assert "Помилка валідації в рядку" in log_content


def test_application_flow_strict_mode_aborts(
    malformed_csv_file: Path,
    tmp_path: Path,
) -> None:
    """У строгому режимі помилка валідації блокує створення файлу."""
    cfg_file = tmp_path / "strict_config.yaml"
    out_file = tmp_path / "strict_out.json"
    log_file = tmp_path / "strict.log"

    cfg_content = (
        f"input:\n  path: {malformed_csv_file.as_posix()}\n"
        f"output:\n  path: {out_file.as_posix()}\n"
        f"processing:\n  minimum_balance: 50.0\n  skip_invalid: false\n"
        f"logging:\n  level: INFO\n  path: {log_file.as_posix()}\n"
    )
    cfg_file.write_text(cfg_content, encoding="utf-8")

    with pytest.raises(RecordValidationError):
        run_pipeline(cfg_file)

    assert not out_file.exists()


def test_main_cli_success(
    sample_config_yaml: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Перевірка виконання точки входу main() через CLI аргументи."""
    monkeypatch.setattr(
        sys,
        "argv",
        ["reliable-importer", "-c", str(sample_config_yaml)],
    )
    main()
    captured = capsys.readouterr()
    assert "Успішно завершено" in captured.out


def test_main_cli_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Перевірка виходу з кодом 1 при помилці в main()."""
    missing_cfg = tmp_path / "non_existent.yaml"
    monkeypatch.setattr(
        sys,
        "argv",
        ["reliable-importer", "-c", str(missing_cfg)],
    )
    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Помилка:" in captured.err
