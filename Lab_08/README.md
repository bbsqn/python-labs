# Лабораторна робота №8: Мережеве та асинхронне програмування. REST API

**Студент:** Зінчук Остап  
**Група:** ФЕП-33  
**Варіант:** 4 («Система банківських рахунків»)  
**Дисципліна:** Професійний Python  
**Викладач:** Проф. Свелеба Сергій Андрійович  
**Львівський національний університет імені Івана Франка**, 2026  

---

## 1. Мета та завдання роботи

- **Мета:** Опанувати принципи мережевої взаємодії на основі HTTP/REST/JSON, розробити вебсервіс із використанням **FastAPI** та **Pydantic v2** поверх наявного сервісного й репозиторного шарів (`SQLAlchemy 2.0` + `SQLite` із Лабораторної роботи №7), а також реалізувати неблокувальні асинхронні операції за допомогою **`async/await`**, **`asyncio.Task`**, **`asyncio.gather()`**, **`asyncio.Semaphore`**, **timeout**, **retry з exponential backoff** та клієнта **`httpx.AsyncClient`**.
- **Завдання за Варіантом 4 («Система банківських рахунків»):**
  1. Продовжити проєкт `bank_system` з підтримкою клієнтів (`clients`), банківських рахунків (`accounts`) та історії транзакцій (`transactions`).
  2. Розробити Pydantic-схеми запитів і відповідей (`schemas.py`) із валідацією (`gt=0`, `ge=0`, `min_length`, `max_length`, `ConfigDict(from_attributes=True)`).
  3. Створити FastAPI-застосунок (`api.py`) із Dependency Injection (`dependencies.py`), `lifespan`-ініціалізацією БД та custom exception handlers (`404`, `400`, `409`, `422`).
  4. Реалізувати REST API endpoints:
     - `GET /` — стан сервісу;
     - `POST /clients`, `GET /clients` — створення та список клієнтів;
     - `POST /accounts`, `GET /accounts` (з фільтрацією та пагінацією `client_id`, `account_type`, `min_balance`, `search`, `limit`, `offset`), `GET /accounts/{account_id}`, `PATCH/PUT /accounts/{account_id}`, `DELETE /accounts/{account_id}`;
     - `POST /accounts/{account_id}/deposit`, `POST /accounts/{account_id}/withdraw`, `GET /accounts/{account_id}/transactions`;
     - `POST /transfers` — атомарний переказ коштів між рахунками;
     - `GET /accounts/statistics` — зведені агрегати балансів;
     - `POST /accounts/batch` — асинхронна агрегація стану кількох рахунків через `httpx.AsyncClient`, `asyncio.Semaphore`, `asyncio.create_task()`, `asyncio.gather()`, `timeout` та `retry`.
  5. Реалізувати автоматичні інтеграційні та асинхронні API-тести (`tests/test_api.py` з `TestClient`, `httpx.AsyncClient`, `ASGITransport`, `MockTransport`).

---

## 2. Структура проєкту

```text
Lab_08/
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
│   └── Проф. Python-Lab_08-Зінчук.pdf
├── src/
│   └── bank_system/
│       ├── __init__.py
│       ├── api.py
│       ├── database.py
│       ├── dependencies.py
│       ├── exceptions.py
│       ├── external_api.py
│       ├── main.py
│       ├── models.py
│       ├── repositories.py
│       ├── schemas.py
│       └── services.py
└── tests/
    ├── conftest.py
    ├── test_api.py
    └── test_repositories.py
```

---

## 3. Команди запуску та перевірки

```bash
# Запуск REST API сервера (Swagger UI доступний за адресою http://127.0.0.1:8000/docs)
python -m uvicorn bank_system.api:app --reload

# Запуск асинхронного демонстраційного сценарію (HTTPX + ASGITransport + Semaphore + gather)
python src/bank_system/main.py

# Запуск API та репозиторних тестів
python -m pytest -v

# Статичний аналіз коду та перевірка типів
python -m flake8 src tests
python -m mypy src tests
```
