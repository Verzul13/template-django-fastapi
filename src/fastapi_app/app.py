
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .asyncdb.auto import refresh_mapping
from .core.django_init import ensure_django_initialized
from .core.exceptions import install_exception_handlers
from .core.middlewares import install_middlewares
from .settings.config import settings
from .settings.logging import enable_udp_logging, setup_logging


def create_app() -> FastAPI:
    setup_logging()

    # ВАЖНО: инициализируем Django ПРЯМО СЕЙЧАС,
    # до импорта роутов и их моделей
    ensure_django_initialized(settings.django_settings_module)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # уже в воркере: безопасно подключаем UDP-хендлер
        enable_udp_logging()
        try:
            await refresh_mapping(force=False)
        except Exception:
            pass

        try:
            yield
        finally:
            # тут можно закрыть ресурсы при shutdown
            pass

    app = FastAPI(
        title=settings.project_name,
        openapi_url=f"{settings.api_prefix}/openapi.json",
        docs_url=f"{settings.api_prefix}/docs" if settings.enable_swagger else None,
        redoc_url=None,
        lifespan=lifespan,
    )

    # Теперь можно подтягивать роуты
    from .routes import include_all_routers

    install_middlewares(app, settings)
    install_exception_handlers(app)
    include_all_routers(app, settings)
    return app
