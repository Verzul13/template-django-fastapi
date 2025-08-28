from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from ..settings.config import Settings
from .django_init import ensure_django_initialized


def install_middlewares(app: FastAPI, settings: Settings):
    # Инициализация Django один раз при старте
    ensure_django_initialized(settings.django_settings_module)

    # CORS
    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[str(o) for o in settings.cors_origins],
            allow_methods=["*"],
            allow_headers=["*"],
            allow_credentials=True,
        )
