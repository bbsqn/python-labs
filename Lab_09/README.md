# Лабораторна робота №9: Паралельність, багатопроцесність та оптимізація

**Студент:** Зінчук Остап  
**Група:** ФЕП-33  
**Варіант:** 4 («Система банківських рахунків»)  
**Дисципліна:** Професійний Python  
**Викладач:** Проф. Свелеба Сергій Андрійович  
**Львівський національний університет імені Івана Франка**, 2026  

---

## 1. Мета та завдання роботи

- **Мета:** Ознайомитися з підходами до паралельного та конкурентного виконання програм у Python, дослідити вплив Global Interpreter Lock (GIL) на CPU-bound та I/O-bound задачі, застосувати `threading`, `multiprocessing`, `ThreadPoolExecutor`, `ProcessPoolExecutor` та синхронізацію через `Lock`; навчитися виявляти вузькі місця (bottlenecks) за допомогою `timeit`, `perf_counter`, `cProfile` і `tracemalloc`, оптимізувати обчислення за допомогою **NumPy** vectorization та **caching** (`@lru_cache` із cache invalidation), а також експериментально підтвердити реальний `speedup`.
- **Завдання за Варіантом 4 («Система банківських рахунків»):**
  1. Зберегти всі базові можливості попередніх лабораторних робіт (REST API на FastAPI, SQLAlchemy 2.0 + SQLite, репозиторії, сервіси, поповнення, списання, перекази, заборона від'ємного балансу).
  2. Створити тестовий набір із **100 000+ рахунків** та **500 000+ операцій** (`analytics.py`).
  3. Профілювати (`cProfile`, `tracemalloc`, `timeit`) обчислення загальної суми коштів, обороту, статистики транзакцій, розрахунку балансу за великою історією та CPU-bound скорингу операцій.
  4. Порівняти **Python loops (baseline)**, **ThreadPoolExecutor**, **ProcessPoolExecutor** (дослідивши `workers = 1, 2, 4, 8` і `chunksize`) та **NumPy** на трьох розмірах даних (`10 000`, `100 000`, `500 000`) із 5 повторами; окремо дослідити I/O-bound читання журналів операцій через `ThreadPoolExecutor` і прямий `threading.Thread` / `multiprocessing.Process`.
  5. Змоделювати конкурентні поповнення та списання у спільній пам'яті (`SharedAccountState`), продемонструвати **race condition** і виправити її через **`threading.Lock`** із перевіркою незмінності фінального балансу.
  6. Застосувати **`@lru_cache`** (`BankAnalyticsLedger`) для повторної статистики транзакцій рахунку з версійним механізмом **cache invalidation** після нових операцій.
  7. Розробити автоматичні тести правильності оптимізації, паралельності, `Lock` і `caching` (`tests/test_parallel.py`).

---

## 2. Структура проєкту

```text
Lab_09/
├── .gitignore
├── alembic.ini
├── conftest.py
├── pyproject.toml
├── README.md
├── setup.cfg
├── benchmarks/
│   ├── benchmark.py
│   ├── benchmark_numpy.py
│   ├── benchmark_processes.py
│   ├── benchmark_statistics.py
│   ├── benchmark_threads.py
│   └── results/
│       ├── benchmark_results.csv
│       ├── cache_results.csv
│       ├── execution_time_chart.png
│       ├── scoring_results.csv
│       ├── speedup_chart.png
│       ├── workers_scaling.csv
│       └── workers_scaling_chart.png
├── migrations/
│   └── ...
├── report/
│   └── Проф. Python-Lab_09-Зінчук.pdf
├── src/
│   └── bank_system/
│       ├── __init__.py
│       ├── analytics.py
│       ├── api.py
│       ├── database.py
│       ├── dependencies.py
│       ├── exceptions.py
│       ├── external_api.py
│       ├── main.py
│       ├── models.py
│       ├── parallel.py
│       ├── profiling.py
│       ├── repositories.py
│       ├── schemas.py
│       └── services.py
└── tests/
    ├── conftest.py
    ├── test_api.py
    ├── test_parallel.py
    └── test_repositories.py
```

---

## 3. Команди запуску та перевірки

```bash
# Демонстрація оптимізації, кешування та Lock-синхронізації
python src/bank_system/main.py

# Профілювання через timeit, cProfile (до/після) та tracemalloc
python src/bank_system/profiling.py

# Повні експериментальні бенчмарки (10k, 100k, 500k; 5 повторів; CSV + графіки)
python benchmarks/benchmark_statistics.py
python benchmarks/benchmark_numpy.py
python benchmarks/benchmark_threads.py
python benchmarks/benchmark_processes.py

# Автоматичні тести (REST API, репозиторії, паралельність, NumPy, Lock, caching)
python -m pytest -v

# Статичний аналіз коду та перевірка типів
python -m flake8 src tests benchmarks
python -m mypy src tests benchmarks
```
