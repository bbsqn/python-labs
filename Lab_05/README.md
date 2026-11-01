# Лабораторна робота №5: Обробка помилок, файли та серіалізація

**Студент:** Зінчук Остап  
**Група:** ФЕП-33  
**Курс:** Професійний Python  
**Викладач:** проф. Свелеба Сергій Андрійович  
**Варіант 4:** Імпорт та експорт системи банківських рахунків  

---

## 1. Опис проєкту

Проєкт реалізує надійний, відмовостійкий виробничий модуль потокового імпорту, валідації, фільтрації та експорту даних банківських рахунків і платіжних операцій із гнучким налаштуванням через YAML-конфігурацію, захистом конфіденційних реквізитів у системі журналювання (logging), власною ієрархією виключень (Custom Exception Hierarchy), ланцюжками виключень (Exception Chaining), підтримкою режимів **Strict** та **Tolerant**, а також гарантією цілісності файлів через атомарний запис (Atomic Write).

### Вхідні дані (CSV)
```csv
account_number,client,balance,operation,amount
```
- `account_number`: унікальний номер банківського рахунку (не порожній);
- `client`: прізвище та ім'я клієнта (не порожнє);
- `balance`: початковий баланс рахунку (`balance >= 0`);
- `operation`: тип операції (`deposit`, `withdraw`);
- `amount`: сума транзакції (`amount > 0`);
- **Бізнес-правило Варіанта 4:** сувора заборона від'ємного балансу після операції зняття (`withdraw` за умови `balance < amount` відхиляється або викликає помилку валідації).

### Вихідні дані (JSON)
Атомарний експорт у структурований JSON-масив з розрахованим фінальним балансом (`new_balance`).

---

## 2. Архітектура надійного конвеєра (Pipeline)

```text
       config.yaml
            │
            ▼
       load_config() ────────► validate_config() (Fail-Fast)
            │
            ▼
      accounts.csv
            │
            ▼
     read_csv_rows() (Streaming generator, yield (line_number, row))
            │
            ▼
      parse_account() ────────► Валідація типів, сум, балансу та овердрафту
            │
       ┌────┴────────────────────────┐
       │                             │
    [ Valid ]                   [ Invalid ]
       │                             │
       ▼                             ▼
BankAccountRecord             RecordValidationError
       │                             │
       │                   ┌─────────┴─────────┐
       │                   ▼                   ▼
       │             Strict Mode         Tolerant Mode
       │             (raise SystemExit)  (logger.warning + skip)
       ▼                                       │
filter_by_balance()                            ▼
       │                              Masked Log & Counter
       ▼
export_accounts_json() (Atomic write: write to .tmp -> replace / unlink on error)
       │
       ▼
 accounts.json
```

---

## 3. Структура проєкту

```text
Lab_05/
├── .gitignore
├── pyproject.toml
├── config.yaml
├── README.md
├── data/
│   └── accounts.csv
├── output/
│   └── accounts.json
├── logs/
│   └── application.log
├── report/
│   └── Проф. Python-Lab_05-Зінчук.pdf    <-- Офіційний звіт у форматі PDF
├── src/
│   └── reliable_importer/
│       ├── __init__.py
│       ├── config.py
│       ├── exceptions.py
│       ├── exporters.py
│       ├── logging_config.py
│       ├── main.py
│       ├── models.py
│       ├── readers.py
│       ├── services.py
│       ├── utils.py
│       └── validators.py
└── tests/
    └── test_importer.py
```

---

## 4. Ключові механізми надійності

1. **Власна ієрархія виключень (`exceptions.py`):**
   - `ApplicationError(Exception)` -> `ConfigurationError`, `DataError`
   - `DataError` -> `DataImportError`, `RecordValidationError`, `DataExportError`
   - `RecordValidationError` зберігає контекст помилки: `line_number` та `field`.
2. **Ланцюжки виключень (Exception Chaining):**
   - Використання синтаксису `raise ... from error` дозволяє зберегти оригінальну технічну першопричину (наприклад, низькорівневий `ValueError` або `OSError`) при переході на доменні виключення.
3. **Політики обробки помилок (Strict vs Tolerant):**
   - **Strict mode (`skip_invalid: false`):** перша ж помилка перериває імпорт для гарантії повної відповідності даних.
   - **Tolerant mode (`skip_invalid: true`):** помилкові рядки логуються як `WARNING`, збільшується лічильник `invalid`, а обробка триває далі.
4. **Захист конфіденційних реквізитів у логах:**
   - Номери рахунків маскуються у формат `UA12****7890`, запобігаючи витоку персональних банківських даних у журнал подій.
5. **Атомарний експорт (Atomic Write):**
   - Запис спочатку здійснюється у тимчасовий файл `.tmp`. Лише після успішного завершення всього циклу файл атомарно замінює цільовий (`replace`). У разі аварійного збою `.tmp` видаляється, а попередній цільовий файл залишається неушкодженим.
6. **Власний Context Manager (`utils.logged_operation`):**
   - Фіксує початок і тривалість кожної критичної операції, а при виникненні виключення записує повний `traceback` через `logger.exception()`.

---

## 5. Результати експериментів

### Експеримент 1: Strict vs Tolerant Mode (1000 валідних + 10 невалідних записів)

| Параметр | Strict Mode (`skip_invalid: false`) | Tolerant Mode (`skip_invalid: true`) |
|---|---|---|
| **Оброблено записів** | 1001 (зупинка на 1-му невалідному) | 1010 (оброблено всі) |
| **Valid** | 1000 | 1000 |
| **Invalid** | 1 | 10 |
| **Exported** | 0 (файл не створюється) | 1000 |
| **Завершення application** | Аварійне переривання (`SystemExit(1)`) | Успішне завершення (Exit code 0) |

*Висновок:* Strict mode доцільний для критичних міжбанківських клірингових реєстрів, де неприпустима втрата жодного запису. Tolerant mode незамінний для імпорту масових аналітичних даних.

### Експеримент 2: Streaming vs Eager (вимірювання пам'яті та часу)

| Кількість записів | Eager Time (s) | Streaming Time (s) | Eager Peak RAM (MB) | Streaming Peak RAM (MB) |
|---|---|---|---|---|
| **10 000** | 0.0693 | 0.0655 | 4.64 | 0.19 |
| **100 000** | 0.6442 | 0.6040 | 44.96 | 0.19 |
| **500 000** | 5.1786 | 5.8735 | 224.34 | 0.19 |

*Висновок:* Потоковий підхід забезпечує константне використання оперативної пам'яті $O(1)$ (~0.19 МБ) навіть на півмільйонних датасетах, тоді як жадібний метод споживає понад 224 МБ RAM ($O(N)$).

### Експеримент 3: Exception Chaining
- При спробі конвертувати рядок `"wrong_number"` у числовий баланс виникає `ValueError: could not convert string to float: 'wrong_number'`.
- Конструкція `raise RecordValidationError(...) from error` формує явний зв'язок у traceback:
  `ValueError` -> `RecordValidationError`, що дозволяє розробнику бачити точну причину та номер рядка.

### Експеримент 4: Атомарний експорт при аварійному збої
- При моделюванні збою під час генерації даних файл `.tmp` був автоматично видалений, оригінальний вихідний файл залишився незмінним, а виключення `DataExportError` було зареєстровано в логах.

### Експеримент 5: Помилки конфігурації
- Система успішно ідентифікує та блокує: відсутність файлу `config.yaml`, синтаксичні помилки YAML, відсутні обов'язкові ключі, від'ємні числові параметри та відсутність вхідного файлу даних на етапі запуску (Fail-Fast).

---

## 6. Запуск та перевірка

### Запуск головного додатку
```bash
python src/reliable_importer/main.py
```

### Запуск модульних тестів (unittest)
```bash
python -m unittest discover -s tests
```

### Перевірка стилю коду (flake8)
```bash
python -m flake8 src tests
```

### Перевірка типізації (mypy)
```bash
python -m mypy src tests
```
