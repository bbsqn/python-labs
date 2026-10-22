"""Модуль генераторів читання та попередньої фільтрації рядків."""

from collections.abc import Iterable, Iterator
from itertools import chain
from pathlib import Path


def read_lines(path: Path) -> Iterator[str]:
    """Генератор читання файлу рядок за рядком із використанням yield from."""
    with path.open("r", encoding="utf-8") as file:
        yield from file


def clean_lines(lines: Iterable[str]) -> Iterator[str]:
    """Генератор очищення рядків від пробілів та пустих рядків."""
    for line in lines:
        cleaned = line.strip()
        if cleaned:
            yield cleaned


def read_files_chain(*paths: Path) -> Iterator[str]:
    """Об'єднує читання кількох файлів у єдиний потік через itertools.chain."""
    iterators = [read_lines(p) for p in paths]
    yield from chain(*iterators)
