# src/fastapi_app/core/django_init.py
"""
Инициализируем Django, чтобы использовать модели/ORM в FastAPI.
Функция идемпотентна: повторные вызовы безопасны.
"""
import os


def ensure_django_initialized(django_settings_module: str) -> None:
    # Проверяем через django.apps.apps, но корректно импортируем его
    try:
        from django.apps import apps as django_apps
        if django_apps.ready:
            return
    except Exception:
        # Если Django ещё не установлен/инициализирован — просто продолжим
        pass

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", django_settings_module)

    # Важно: импортировать django и вызвать setup только сейчас
    import django  # noqa: WPS433 (runtime import — осознанно)
    django.setup()
