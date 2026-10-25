"""Модуль узагальненого репозиторію (Generic Repository)."""

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from .protocols import HasId

T = TypeVar("T", bound=HasId)


class Repository(Generic[T], ABC):
    """Абстрактний інтерфейс узагальненого сховища сутностей."""

    @abstractmethod
    def add(self, item: T) -> None:
        """Додає сутність у сховище."""
        ...

    @abstractmethod
    def get(self, item_id: Any) -> T | None:
        """Отримує сутність за ідентифікатором."""
        ...

    @abstractmethod
    def all(self) -> list[T]:
        """Повертає список усіх сутностей."""
        ...

    @abstractmethod
    def remove(self, item_id: Any) -> bool:
        """Видаляє сутність за ідентифікатором."""
        ...

    @abstractmethod
    def count(self) -> int:
        """Повертає загальну кількість елементів."""
        ...


class InMemoryRepository(Repository[T]):
    """Потокобезпечна in-memory реалізація репозиторію."""

    def __init__(self) -> None:
        self._items: dict[Any, T] = {}

    def add(self, item: T) -> None:
        self._items[item.id] = item

    def get(self, item_id: Any) -> T | None:
        return self._items.get(item_id)

    def all(self) -> list[T]:
        return list(self._items.values())

    def remove(self, item_id: Any) -> bool:
        return self._items.pop(item_id, None) is not None

    def count(self) -> int:
        return len(self._items)
