# Bank Account Service

Production-ready REST API, persistence layer, and analytics service for the **Bank Account System** (Laboratory Work №10, Variant 4).

**Студент:** Зінчук Остап  
**Група:** ФЕП-33  
**Дисципліна:** Професійний Python  
**Викладач:** Проф. Свелеба Сергій Андрійович  
**Львівський національний університет імені Івана Франка**, 2026

---

## Description

`bank-account-service` completes the incremental development of the Bank Account System (`Lab_01`–`Lab_10`): modular domain design, SQLAlchemy 2.0 ORM persistence and Alembic migrations, FastAPI REST API + async HTTPX batch processing, NumPy-vectorized analytics + `@lru_cache` + `threading.Lock`, environment-based configuration, Docker containerization, installable Python packaging (`wheel` and `sdist`), and GitHub Actions CI/CD.

---

## Features

- Full domain workflow: client registration, bank account opening, deposits, withdrawals, balance checks, account search/filtering, total funds/turnover statistics, transaction history, atomic money transfers with rollback, and strict non-negative balance enforcement.
- Environment-driven configuration via Pydantic `BaseSettings` (`ENVIRONMENT` / `APP_ENV`, `DATABASE_URL`, `LOG_LEVEL`, `APP_NAME`, optional `API_KEY` — zero secrets committed to Git).
- Production logging (`logging`) and `GET /health` endpoint with Docker `HEALTHCHECK`.
- Optimized analytics (`analytics.py`, `parallel.py`) using NumPy vectorization, `@lru_cache` with version invalidation, and `threading.Lock`.
- Multi-stage `Dockerfile` running as a non-root user (`appuser`) with SQLite persistent volume support.
- Automated GitHub Actions CI pipeline: Ruff lint & format check, `mypy --strict`, `pytest` with coverage, `python -m build`, and Docker image build verification.

---

## Requirements

- Python `>=3.11`
- Optional: Docker (for building and running containers locally)

---

## Installation

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# Linux/macOS: source .venv/bin/activate

python -m pip install --upgrade pip
pip install -e ".[dev]"
```

Build installable `wheel` and `sdist` packages:

```bash
python -m build
```

---

## Configuration

Copy `.env.example` to `.env` (never commit `.env` or any real secrets):

```bash
cp .env.example .env
```

Supported environment variables:

| Variable | Description | Default |
|---|---|---|
| `APP_NAME` | Service display title in FastAPI/OpenAPI | `Bank Account Service` |
| `ENVIRONMENT` (or `APP_ENV`) | Runtime environment (`development`, `test`, `production`) | `development` |
| `DATABASE_URL` | SQLAlchemy connection string | `sqlite:///./bank_account_service.db` |
| `LOG_LEVEL` | Standard Python logging level (`INFO`, `DEBUG`, `WARNING`) | `INFO` |
| `API_KEY` | Optional external integration token (kept outside Git) | `None` |

Example PowerShell override without editing source code:

```powershell
$env:ENVIRONMENT="production"
$env:LOG_LEVEL="DEBUG"
```

---

## Running locally

Start the REST API with Uvicorn:

```bash
uvicorn bank_account_service.api:app --host 127.0.0.1 --port 8000 --reload
```

Or run the packaged console script entrypoint:

```bash
bank-account-service
```

---

## Running with Docker

Build the multi-stage production image:

```bash
docker build -t bank-account-service:1.0.0 .
```

Run container with environment variables and persistent SQLite volume:

```bash
docker run --rm -p 8000:8000 \
  -v bank_data:/app/data \
  -e ENVIRONMENT=production \
  -e LOG_LEVEL=INFO \
  -e DATABASE_URL=sqlite:////app/data/bank_account_service.db \
  bank-account-service:1.0.0
```

Verify health endpoint:

```bash
curl http://127.0.0.1:8000/health
```

---

## API

Interactive API documentation is generated automatically by FastAPI:
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`
- OpenAPI JSON schema: `http://127.0.0.1:8000/openapi.json`

Core Variant 4 endpoints:
- `GET /health` — service healthcheck and active runtime environment
- `GET /` — API status message and version (`1.0.0`)
- `POST /clients`, `GET /clients` — register and list clients
- `POST /accounts`, `GET /accounts`, `GET /accounts/{account_id}`, `PATCH/PUT /accounts/{account_id}`, `DELETE /accounts/{account_id}` — full account CRUD, filtering, and pagination
- `POST /accounts/{account_id}/deposit`, `POST /accounts/{account_id}/withdraw` — deposit/withdrawal operations
- `GET /accounts/{account_id}/transactions` — transaction history for an account
- `POST /transfers` — atomic balance transfer between accounts
- `GET /accounts/statistics` — aggregated total funds, average balance, and per-client totals
- `POST /accounts/batch` — concurrent HTTPX batch account summary

---

## Testing

```bash
pytest -v --cov=bank_account_service --cov-report=term-missing
ruff check .
ruff format --check .
mypy src tests
```

---

## Project structure

```text
Lab_10/
├── .github/
│   └── workflows/
│       └── ci.yml
├── benchmarks/
├── migrations/
├── report/
│   └── Проф. Python-Lab_10-Зінчук.pdf
├── src/
│   └── bank_account_service/
│       ├── __init__.py
│       ├── analytics.py
│       ├── api.py
│       ├── config.py
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
├── tests/
│   ├── conftest.py
│   ├── test_api.py
│   ├── test_config_and_health.py
│   ├── test_parallel.py
│   └── test_repositories.py
├── .dockerignore
├── .env.example
├── .gitignore
├── alembic.ini
├── conftest.py
├── Dockerfile
├── LICENSE
├── pyproject.toml
└── README.md
```

---

## CI/CD

GitHub Actions workflow (`.github/workflows/ci.yml`) runs automatically on `push` and `pull_request` across Python `3.11` and `3.12`:
1. `ruff check .` (lint)
2. `ruff format --check .` (code formatting)
3. `mypy src tests` (strict static typing)
4. `pytest -v --cov=bank_account_service --cov-report=term-missing`
5. `python -m build` (wheel and sdist build check)
6. `docker build` and live `/health` verification inside the container

---

## Authors

- **Зінчук Остап**, студент групи ФЕП-33, Львівський національний університет імені Івана Франка
