from typing import List

from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Бизнес-настройки
    project_name: str = "FastAPI endpoints"
    api_prefix: str = "/api"
    enable_swagger: bool = True

    # CORS
    cors_origins: List[AnyHttpUrl] = []

    # Логи
    log_level: str = "INFO"
    uvicorn_access_log: bool = True

    # Интеграция с Django
    django_settings_module: str = "django_project.settings"

    model_config = SettingsConfigDict(env_prefix="FASTAPI_", env_file=None, extra="ignore")


# Один экземпляр настроек, читающий ENV (FASTAPI_*)
settings = Settings()
