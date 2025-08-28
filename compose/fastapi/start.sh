#!/usr/bin/env bash
set -e
# Запуск Uvicorn (FastAPI)
: "${UVICORN_WORKERS:=2}"
exec uvicorn fastapi_app.main:app --host 0.0.0.0 --port 8001 --workers "${UVICORN_WORKERS}"
