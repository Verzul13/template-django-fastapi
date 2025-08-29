#!/usr/bin/env bash
set -e

: "${DEBUG:=0}"

if [ "$DEBUG" = "1" ]; then
  echo "[django] DEV mode: runserver + migrate"
  python /app/src/manage.py migrate --noinput
  exec python /app/src/manage.py runserver 0.0.0.0:8000
else
  echo "[django] PROD mode: gunicorn + migrate + collectstatic"
  python /app/src/manage.py migrate --noinput
  python /app/src/manage.py collectstatic --noinput
  exec gunicorn django_project.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers "${GUNICORN_WORKERS:-4}" \
    --threads "${GUNICORN_THREADS:-2}" \
    --timeout "${GUNICORN_TIMEOUT:-90}"
fi
