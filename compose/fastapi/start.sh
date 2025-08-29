#!/usr/bin/env bash
set -e

: "${UVICORN_WORKERS:=2}"
: "${DEBUG:=0}"

if [ "$DEBUG" = "1" ]; then
  echo "[fastapi] DEV mode: uvicorn --reload"
  exec uvicorn fastapi_app.main:app \
    --host 0.0.0.0 \
    --port 8001 \
    --reload \
    --reload-dir /app/src
else
  echo "[fastapi] PROD mode: uvicorn --workers=${UVICORN_WORKERS}"
  exec uvicorn fastapi_app.main:app \
    --host 0.0.0.0 \
    --port 8001 \
    --workers "${UVICORN_WORKERS}"
fi
