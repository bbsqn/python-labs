from typing import Any

"""Модуль початкових структурованих даних банківських рахунків."""

# Список словників (list of dicts) - основний набір даних
accounts: list[dict[str, Any]] = [
    {
        "id": 1,
        "account_number": "UA100001",
        "client_name": "Олена Ткаченко",
        "balance": 15230.50,
        "account_type": "savings",
        "currency": "UAH",
    },
    {
        "id": 2,
        "account_number": "UA100002",
        "client_name": "Іван Петренко",
        "balance": 4800.00,
        "account_type": "debit",
        "currency": "UAH",
    },
    {
        "id": 3,
        "account_number": "UA100003",
        "client_name": "Марія Коваль",
        "balance": 980.75,
        "account_type": "credit",
        "currency": "UAH",
    },
    {
        "id": 4,
        "account_number": "UA100004",
        "client_name": "Олена Ткаченко",
        "balance": 250.00,
        "account_type": "debit",
        "currency": "UAH",
    },
    {
        "id": 5,
        "account_number": "UA100005",
        "client_name": "Василь Бойко",
        "balance": 42100.00,
        "account_type": "deposit",
        "currency": "UAH",
    },
    {
        "id": 6,
        "account_number": "UA100006",
        "client_name": "Оксана Шевченко",
        "balance": 8750.25,
        "account_type": "savings",
        "currency": "UAH",
    },
    {
        "id": 7,
        "account_number": "UA100007",
        "client_name": "Дмитро Мельник",
        "balance": 3100.00,
        "account_type": "business",
        "currency": "UAH",
    },
    {
        "id": 8,
        "account_number": "UA100008",
        "client_name": "Ірина Бондар",
        "balance": 19500.80,
        "account_type": "deposit",
        "currency": "UAH",
    },
    {
        "id": 9,
        "account_number": "UA100009",
        "client_name": "Тарас Новак",
        "balance": 150.00,
        "account_type": "credit",
        "currency": "UAH",
    },
    {
        "id": 10,
        "account_number": "UA100010",
        "client_name": "Андрій Лисенко",
        "balance": 6420.00,
        "account_type": "business",
        "currency": "UAH",
    },
]

# Кортеж (tuple) для демонстрації незмінюваної структури
ACCOUNTS_TUPLE: tuple[dict[str, Any], ...] = tuple(accounts)

# Множина (set) унікальних типів рахунків
ACCOUNT_TYPES: set[str] = {acc["account_type"] for acc in accounts}

# Студентські аліаси для зворотної сумісності з тестами з прикладу
students = [
    {
        "id": acc["id"],
        "name": acc["client_name"],
        "group": acc["account_type"],
        "grade": acc["balance"],
    }
    for acc in accounts
]
