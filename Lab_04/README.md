# Лабораторна робота №4: Професійне ООП та система типів Python

**Студент:** Зінчук Остап  
**Група:** ФЕП-33  
**Курс:** Професійний Python  
**Варіант 4:** Система банківських рахунків  

---

## 1. Опис проєкту

Проєкт реалізує типізовану об'єктно-орієнтовану модель банківської системи з розділенням на доменний та сервісний рівні, використанням незмінюваних об'єктів-значень (Value Objects), абстрактних базових класів (ABC), протоколів структурної типізації (Protocol), узагальнених сховищ (Generic Repository) та впровадження залежностей (Dependency Injection).

### Предметна область (Варіант 4)
- **Domain Entities:** `Account` (ABC), `SavingsAccount`, `CurrentAccount`, `Customer`, `Transaction`, `BankRegistry`.
- **Value Objects:** `Money` (frozen, slots, з арифметичними операціями та валідацією валюти).
- **Abstractions / Strategies:** `FeePolicy` (ABC) -> `ZeroFeePolicy`, `PercentageFeePolicy`.
- **Protocols:** `HasId` (bound TypeVar constraint), `Notifier` (повідомлення клієнтам).
- **Generic Repository:** `Repository[T]` (ABC) -> `InMemoryRepository[T]`.
- **Application Service:** `BankingService` (оркестрація бізнес-операцій, відкриття рахунків, перекази, контроль балансу).
- **DTO / TypedDict:** `CustomerPayload`, `AccountPayload`, `TransactionPayload`.

### Ключові бізнес-правила
1. **Заборона від'ємного балансу:** операції зняття коштів (`withdraw`) як на ощадних, так і на поточних рахунках перевіряють достатність коштів. При спробі перевести баланс у від'ємне значення викидається `ValueError`.
2. **Ощадний рахунок (`SavingsAccount`):** підтримує незнижуваний залишок (`minimum_balance`) та нарахування річних відсотків (`apply_interest`).
3. **Поточний рахунок (`CurrentAccount`):** підтримує динамічну політику комісій (`FeePolicy`), що передається через композицію.

---

## 2. Діаграма класів (Class Diagram)

```text
                  ┌────────────────────────┐
                  │      FeePolicy (ABC)   │
                  └───────────▲────────────┘
                              │
                ┌─────────────┴─────────────┐
                │                           │
    ┌───────────────────────┐   ┌───────────────────────┐
    │     ZeroFeePolicy     │   │  PercentageFeePolicy  │
    └───────────────────────┘   └───────────────────────┘
                                            ▲
                                            │ has-a (composition)
  ┌──────────────────┐          ┌───────────┴───────────┐
  │     Customer     │◄─────────┤     Account (ABC)     │
  └──────────────────┘  has-a   └───────────▲───────────┘
                                            │
                               ┌────────────┴────────────┐
                               │                         │
                  ┌─────────────────────────┐  ┌─────────────────────────┐
                  │      SavingsAccount     │  │      CurrentAccount     │
                  └─────────────────────────┘  └─────────────────────────┘
                               ▲                         ▲
                               │                         │
                               └────────────┬────────────┘
                                            │ stores
                               ┌────────────┴────────────┐
                               │       BankRegistry      │
                               │   (Custom Collection)   │
                               └─────────────────────────┘

  ┌──────────────────────────────────────────────────────────────┐
  │                        BankingService                        │
  │   - account_repo: Repository[Account]                        │
  │   - customer_repo: Repository[Customer]                      │
  │   - notifier: Notifier (Protocol)                            │
  └──────────────────────────────────────────────────────────────┘
```

---

## 3. Структура проєкту

```text
Lab_04/
├── .gitignore
├── pyproject.toml
├── README.md
├── report/
│   └── Проф. Python-Lab_04-Зінчук.pdf    <-- Офіційний звіт у форматі PDF
├── src/
│   └── domain_app/
│       ├── __init__.py
│       ├── dto.py
│       ├── main.py
│       ├── models.py
│       ├── protocols.py
│       ├── repositories.py
│       ├── services.py
│       └── value_objects.py
└── tests/
    └── test_domain.py
```

---

## 4. Вимоги методички та їхня реалізація

| Вимога методички | Реалізація в проєкті | Опис |
|---|---|---|
| Не менше 5 domain classes | `Account`, `SavingsAccount`, `CurrentAccount`, `Customer`, `Transaction`, `BankRegistry` | Повноцінна об'єктна модель предметної області |
| Щонайменше 2 dataclass | `Customer`, `Transaction`, `Money` | Автоматична генерація методів та лаконічний опис полів |
| Frozen value object | `Money(frozen=True, slots=True)` | Захист цілісності грошових сум, арифметичні методи з валідацією валюти |
| Property | `Account.balance`, `Account.id`, `Customer.display_name` | Контрольований доступ до приватних атрибутів |
| Inheritance | `SavingsAccount(Account)`, `CurrentAccount(Account)` | Спеціалізація поведінки банківських рахунків (is-a) |
| Composition | `Account has Customer`, `CurrentAccount has FeePolicy`, `Account has list[Transaction]` | Гнучка компоновка функціоналу через делегування (has-a) |
| Abstract Base Class (ABC) | `Account(ABC)`, `FeePolicy(ABC)`, `Repository(Generic[T], ABC)` | Жорсткий контракт інтерфейсу з `@abstractmethod` |
| Protocol | `Notifier(Protocol)`, `HasId(Protocol)` | Качина та структурна типізація (Duck Typing) |
| Щонайменше 3 dunder methods | `__len__`, `__iter__`, `__contains__`, `__getitem__`, `__add__`, `__sub__`, `__eq__`, `__lt__` | Природна інтеграція з базовою об'єктною моделлю Python |
| Dependency Injection | `BankingService(account_repo, customer_repo, notifier)` | Передача зовнішніх залежностей через конструктор |
| Принципи SOLID | SRP, OCP, LSP, ISP, DIP | Архітектурна ізоляція відповідальностей та слабка зв'язність |
| Generic class & TypeVar | `T = TypeVar("T", bound=HasId)`, `Repository[T]` | Повторно використовуване узагальнене сховище даних |
| TypedDict | `CustomerPayload`, `AccountPayload`, `TransactionPayload` | Статична перевірка структури зовнішніх даних (JSON / API) |
| Перевірка mypy | `Success: no issues found in 9 source files` | Повна валідація бази коду в режимі `strict = true` |

---

## 5. Запуск та тестування

### Запуск головного демонстраційного сценарію
```bash
python src/domain_app/main.py
```

### Запуск модульних тестів (unittest)
```bash
python -m unittest discover -s tests
```

### Перевірка відповідності стилю коду (flake8)
```bash
python -m flake8 src tests
```

### Перевірка статичної типізації (mypy)
```bash
python -m mypy src tests
```
