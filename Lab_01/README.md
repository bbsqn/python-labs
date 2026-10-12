# Bank System
Навчальний проєкт з дисципліни «Професійний Python».
Індивідуальний варіант 4 — «Система банківських рахунків».

## Description
Консольний застосунок для роботи з банківськими рахунками:
поповнення, списання коштів, перевірка балансу, пошук рахунку
та обчислення загальної суми коштів.
Не дозволяється отримувати від'ємний баланс.

## Requirements
Python 3.11+

## Installation
```bash
python -m venv .venv
```
Активувати virtual environment, потім:
```bash
python -m pip install -e .
```

## Run
```bash
python -m bank_system.main
```
або через console command:
```bash
bank-system
```

## Project structure
`src/bank_system/models.py`
Data models (Account).

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

## Author
Student: Зінчук Остап
Group: ФЕП-33
