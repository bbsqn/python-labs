"""Модуль доменної ієрархії виключень (Custom Exception Hierarchy)."""


class ApplicationError(Exception):
    """Базове виключення додатку."""


class ConfigurationError(ApplicationError):
    """Помилка валідації або завантаження конфігурації."""


class DataError(ApplicationError):
    """Базове виключення обробки даних."""


class DataImportError(DataError):
    """Помилка читання або імпорту вхідних даних."""


class RecordValidationError(DataError):
    """Помилка валідації окремого запису з контекстом номеру рядка та поля."""

    def __init__(
        self,
        message: str,
        *,
        line_number: int | None = None,
        field: str | None = None,
    ) -> None:
        super().__init__(message)
        self.line_number = line_number
        self.field = field


class DataExportError(DataError):
    """Помилка експорту або збереження вихідних даних."""
