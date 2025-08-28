#!/usr/bin/env bash
set -e
echo "Waiting for Postgres at ${POSTGRES_HOST}:${POSTGRES_PORT}..."
until pg_isready -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" > /dev/null 2>&1; do
  sleep 1
done
echo "Postgres is ready."

# Запуск Celery Beat с Django DatabaseScheduler
exec celery -A django_project beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
