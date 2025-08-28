#!/usr/bin/env bash
set -e

echo "Waiting for Postgres at ${POSTGRES_HOST}:${POSTGRES_PORT}..."
until pg_isready -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" > /dev/null 2>&1; do
  sleep 1
done
echo "Postgres is ready."

# Ensure dirs exist
mkdir -p /app/staticfiles /app/media

# Migrations + collectstatic
python /app/src/manage.py migrate --noinput
python /app/src/manage.py collectstatic --noinput

exec "$@"
