FROM python:3.12-slim AS builder
WORKDIR /app

COPY pyproject.toml poetry.lock* /app/

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir poetry \
    && poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --without dev --no-root

FROM python:3.12-slim
WORKDIR /app

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY events_app/ /app/events_app/
COPY events/     /app/events/
COPY manage.py   /app/
COPY entrypoint.sh /app/

ENV PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=events_app.settings \
    PYTHONPATH=/app

EXPOSE 8000

RUN adduser --disabled-password --no-create-home django && \
    mkdir -p /app/staticfiles && \
    chown -R django:django /app && \
    chmod +x /app/entrypoint.sh

USER django

CMD ["/app/entrypoint.sh"]
