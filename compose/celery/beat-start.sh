#!/usr/bin/env bash
set -e

echo "Waiting for Postgres at ${POSTGRES_HOST}:${POSTGRES_PORT}..."
until pg_isready -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" >/dev/null 2>&1; do
  sleep 1
done
echo "Postgres is ready."

: "${DEBUG:=0}"
: "${CELERY_WORKER_LOGLEVEL:=info}"

BASE_CMD=(celery -A django_project beat -l "${CELERY_BEAT_LOGLEVEL}" --scheduler django_celery_beat.schedulers:DatabaseScheduler)

if [ "${DEBUG}" != "1" ]; then
  echo "Starting Celery beat (prod): ${BASE_CMD[*]}"
  exec "${BASE_CMD[@]}"
fi

# DEV: автоперезапуск через watchfiles / watchdog
SRC_DIR="/app/src"

if command -v watchfiles >/dev/null 2>&1; then
  echo "[celery_beat] DEV: autoreload via watchfiles on ${SRC_DIR}"
  CMD_STR="celery -A django_project beat -l ${CELERY_BEAT_LOGLEVEL} --scheduler django_celery_beat.schedulers:DatabaseScheduler"
  exec watchfiles --target-type=command --filter python "$CMD_STR" "$SRC_DIR"
elif command -v watchmedo >/dev/null 2>&1; then
  echo "[celery_beat] DEV: autoreload via watchmedo on ${SRC_DIR}"
  exec watchmedo auto-restart --directory="${SRC_DIR}" --pattern="*.py" --recursive -- \
       celery -A django_project beat -l "${CELERY_BEAT_LOGLEVEL}" --scheduler django_celery_beat.schedulers:DatabaseScheduler
else
  echo "[celery_beat] DEV: no watch tool found; running without autoreload"
  exec celery -A django_project beat -l "${CELERY_BEAT_LOGLEVEL}" --scheduler django_celery_beat.schedulers:DatabaseScheduler
fi

