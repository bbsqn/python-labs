"""Модуль структурних інтерфейсів (Protocols)."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class HasId(Protocol):
    """Протокол для сутностей із числовим або рядковим ідентифікатором."""

    @property
    def id(self) -> int | str:
        """Повертає унікальний ідентифікатор сутності."""
        ...


@runtime_checkable
class Notifier(Protocol):
    """Протокол для відправки повідомлень клієнтам."""

    def send(self, recipient: str, message: str) -> None:
        """Надсилає повідомлення заданому адресату."""
        ...
