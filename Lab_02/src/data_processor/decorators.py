"""Модуль декораторів для логування, заміру часу та повторення."""

from functools import wraps
from time import perf_counter
from typing import Any, Callable


def measure_time(func: Callable[..., Any]) -> Callable[..., Any]:
    """Декоратор для заміру часу виконання функції."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start = perf_counter()
        result = func(*args, **kwargs)
        elapsed = perf_counter() - start
        print(f"{func.__name__}: {elapsed:.8f} s")
        return result

    return wrapper


def log_call(func: Callable[..., Any]) -> Callable[..., Any]:
    """Декоратор для логування входу і виходу з функції."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        print(f"Calling {func.__name__}")
        result = func(*args, **kwargs)
        print(f"Finished {func.__name__}")
        return result

    return wrapper


def repeat(
    count: int = 1,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Параметризований декоратор (closure) для повторного виклику функції."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            result: Any = None
            for _ in range(count):
                result = func(*args, **kwargs)
            return result

        return wrapper

    return decorator
