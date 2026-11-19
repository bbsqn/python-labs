# Лабораторна робота №7: Робота з базами даних у Python

**Студент:** Зінчук Остап  
**Група:** ФЕП-33  
**Варіант:** 4 («Система банківських рахунків»)  
**Дисципліна:** Професійний Python  
**Викладач:** Проф. Свелеба Сергій Андрійович  
**Львівський національний університет імені Івана Франка**, 2026  

---

## 1. Мета та завдання роботи

- **Мета:** Опанувати принципи організації шару збереження даних (*persistence layer*) у Python-застосунках із використанням реляційної СКБД **SQLite**, стандарту **Python DB-API** (`sqlite3`), параметризованих SQL-запитів, **SQLAlchemy 2.0 ORM**, патерну **Repository**, **ACID**-транзакцій (`commit` / `rollback`), міграцій **Alembic** та інтеграційних тестів на ізольованій тестовій БД.
- **Завдання за Варіантом 4 («Система банківських рахунків»):**
  1. Продовжити проєкт `Lab_01` (`bank_system`) з підтримкою клієнтів, банківських рахунків та забороною від'ємного балансу.
  2. Спроєктувати та реалізувати три пов'язані таблиці: `clients`, `accounts`, `transactions` (PRIMARY KEY, FOREIGN KEY з `PRAGMA foreign_keys=ON`, UNIQUE, CHECK constraints).
  3. Реалізувати окремі репозиторії `ClientRepository`, `AccountRepository`, `TransactionRepository` (повний CRUD та JOIN-пошук).
  4. Реалізувати параметризований пошук рахунку за номером засобами чистого Python DB-API (`find_account_by_number_dbapi`).
  5. Реалізувати сервісний шар `BankService` з операціями `deposit`, `withdraw`, `check_balance`, SQL-агрегаціями (`SUM`, `AVG`, `COUNT`, `GROUP BY`) та атомарною транзакцією `transfer_money()` з `commit()` та `rollback()`.
  6. Налаштувати Alembic та виконати міграції (ініціалізація схеми + додавання колонок `account_type` і `created_at` до таблиці `accounts` з підтримкою `upgrade` і `downgrade`).
  7. Розробити інтеграційні тести в `tests/` з використанням окремої тестової SQLite бази.

---

## 2. Структура проєкту

```text
Lab_07/
├── .gitignore
├── alembic.ini
├── conftest.py
├── pyproject.toml
├── README.md
├── setup.cfg
├── migrations/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       ├── 0001_initial_schema.py
│       └── 0002_add_account_type_and_created_at.py
├── report/
│   └── Проф. Python-Lab_07-Зінчук.pdf
├── src/
│   └── bank_system/
│       ├── __init__.py
│       ├── database.py
│       ├── exceptions.py
│       ├── main.py
│       ├── models.py
│       ├── repositories.py
│       └── services.py
└── tests/
    ├── conftest.py
    ├── test_repositories.py
    └── test_services_and_db_api.py
```

---

## 3. Команди запуску та перевірки

```bash
# Застосування міграцій Alembic
python -m alembic upgrade head
python -m alembic current

# Запуск демонстраційної програми
python src/bank_system/main.py

# Запуск інтеграційних тестів
python -m pytest -v

# Статичний аналіз коду та перевірка типів
python -m flake8 src tests
python -m mypy src tests
```
