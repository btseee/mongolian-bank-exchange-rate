# Mongolian bank exchange-rate API - Docker image
FROM python:3.13-slim AS base

WORKDIR /app

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    PORT=8000

COPY requirements.txt .
RUN python -m pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

RUN playwright install --with-deps chromium

COPY . .

# ============ Test Stage ============
FROM base AS test
RUN pytest --cov=app --cov-report=term-missing -v

# ============ Production Stage ============
FROM base AS production

RUN adduser --disabled-password --gecos "" appuser \
    && mkdir -p /app/logs \
    && chown -R appuser:appuser /app /ms-playwright
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD ["python", "-c", "import requests; requests.get('http://localhost:8000/health', timeout=5)"]

CMD ["sh", "-c", "uvicorn app.api.api:app --host 0.0.0.0 --port $PORT"]

