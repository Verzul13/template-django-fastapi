#!/usr/bin/env bash
set -e
# Ожидание Postgres — на всякий случай, чтобы задачи с БД не падали при старте
echo "Waiting for Postgres at ${POSTGRES_HOST}:${POSTGRES_PORT}..."
until pg_isready -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" > /dev/null 2>&1; do
  sleep 1
done
echo "Postgres is ready."

# Запуск Celery worker
exec celery -A django_project worker -l info
