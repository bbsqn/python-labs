"""Утиліти діагностики та контекстні менеджери."""

from collections.abc import Iterator
from contextlib import contextmanager
import logging
from time import perf_counter

logger = logging.getLogger(__name__)


@contextmanager
def logged_operation(operation: str) -> Iterator[None]:
    """Контекстний менеджер для хронометражу та журналювання операції."""
    logger.info("Операція '%s' розпочата", operation)
    start = perf_counter()
    try:
        yield
    except Exception:
        logger.exception("Операція '%s' перервана з помилкою", operation)
        raise
    else:
        elapsed = perf_counter() - start
        logger.info(
            "Операція '%s' завершена успішно за %.6f с",
            operation,
            elapsed,
        )
