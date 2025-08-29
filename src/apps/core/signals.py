# src/apps/core/signals.py
import logging
import os
import threading

import requests
from django.db.models.signals import post_migrate
from django.dispatch import receiver

log = logging.getLogger("logger")

FASTAPI_INTERNAL_URL = os.getenv("FASTAPI_INTERNAL_URL", "http://fastapi:8001")
FASTAPI_REFRESH_TOKEN = os.getenv("FASTAPI_REFRESH_TOKEN", "")


def _notify_fastapi():
    try:
        url = f"{FASTAPI_INTERNAL_URL}/api/_internal/refresh-mapping"
        headers = {"X-Internal-Token": FASTAPI_REFRESH_TOKEN} if FASTAPI_REFRESH_TOKEN else {}
        resp = requests.post(url, headers=headers, timeout=5)
        log.info("Notified FastAPI to refresh mapping: %s %s", resp.status_code, resp.text[:200])
    except Exception as e:
        log.warning("Failed to notify FastAPI to refresh mapping: %s", e)


@receiver(post_migrate)
def post_migrate_handler(sender, **kwargs):
    # Чтобы не блокировать миграции — делаем вызов в отдельном потоке
    threading.Thread(target=_notify_fastapi, daemon=True).start()
