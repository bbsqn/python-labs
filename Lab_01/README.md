# Bank System
Лабораторна робота №1 з дисципліни «Професійний Python».
Індивідуальний варіант 4 — «Система банківських рахунків».

## Description

Консольний застосунок для роботи з банківськими рахунками:
поповнення, списання коштів, перевірка балансу, пошук рахунку
та обчислення загальної суми коштів банку.
Від'ємний баланс не допускається.

## Requirements

Python 3.11+

## Installation

```
python -m venv .venv
```

Активувати virtual environment, потім:

```
python -m pip install -e .
```

## Run

```
python -m bank_system.main
```

або через console command:

```
bank-system
```

### Приклад запуску

```
Демонстраційні дані завантажено.

--- Система банківських рахунків ---
1. Показати всі рахунки
2. Поповнити рахунок
3. Зняти кошти
4. Перевірити баланс
5. Знайти рахунок(и)
6. Загальна сума коштів банку
7. Рахунки, відсортовані за балансом
8. Найбагатший клієнт
9. Вийти
Оберіть команду: 1

Номер       Клієнт                      Баланс
UA100001    Олена Ткаченко            15230.50 UAH
UA100002    Іван Петренко              4800.00 UAH
UA100003    Марія Коваль                980.75 UAH
UA100004    Олена Ткаченко              250.00 UAH
```

## Project structure

`src/bank_system/models.py`
Data model (Account).

`src/bank_system/services.py`
Business logic: deposit, withdraw, search, statistics.

`src/bank_system/exceptions.py`
Custom exceptions (BankError and subclasses).

`src/bank_system/config.py`
Configuration constants (MIN_BALANCE, CURRENCY).

`src/bank_system/main.py`
Application entry point, menu-driven interface.

`tests/test_services.py`
Unit tests for business logic.
