FROM python:3.12-slim AS builder

WORKDIR /build

COPY pyproject.toml .
COPY README.md .
COPY LICENSE .
COPY src ./src

RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir build \
    && python -m build --wheel

FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_NAME="Bank Account Service" \
    ENVIRONMENT="production" \
    DATABASE_URL="sqlite:////app/data/bank_account_service.db" \
    LOG_LEVEL="INFO"

RUN useradd --create-home --shell /bin/bash appuser \
    && mkdir -p /app/data \
    && chown -R appuser:appuser /app

COPY --from=builder /build/dist/*.whl /tmp/

RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir /tmp/*.whl \
    && rm -rf /tmp/*.whl

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"

CMD ["uvicorn", "bank_account_service.api:app", "--host", "0.0.0.0", "--port", "8000"]
