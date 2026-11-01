"""Модуль утиліт та власних context managers."""

from collections.abc import Iterator
from contextlib import contextmanager
import logging
from time import perf_counter

logger = logging.getLogger(__name__)


@contextmanager
def logged_operation(operation: str) -> Iterator[None]:
    """Власний контекстний менеджер для фіксації початку, завершення,

    тривалості або збою операції з реєстрацією у логах.
    """
    logger.info("Операцію '%s' розпочато", operation)
    start = perf_counter()
    try:
        yield
    except Exception:
        logger.exception("Операція '%s' завершилася збоєм", operation)
        raise
    else:
        elapsed = perf_counter() - start
        logger.info(
            "Операцію '%s' успішно завершено за %.6f с",
            operation,
            elapsed,
        )
