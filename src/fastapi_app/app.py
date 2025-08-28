# fastapi_app/app.py
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .core.django_init import ensure_django_initialized
from .core.exceptions import install_exception_handlers
from .core.middlewares import install_middlewares
from .settings.config import settings
from .settings.logging import enable_udp_logging, setup_logging


def create_app() -> FastAPI:
    setup_logging()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # уже в воркере, можно безопасно подключить UDP-хендлер
        enable_udp_logging()
        yield

    app = FastAPI(
        title=settings.project_name,
        openapi_url=f"{settings.api_prefix}/openapi.json",
        docs_url=f"{settings.api_prefix}/docs" if settings.enable_swagger else None,
        redoc_url=None,
        lifespan=lifespan,
    )

    ensure_django_initialized(settings.django_settings_module)
    from .routes import include_all_routers

    install_middlewares(app, settings)
    install_exception_handlers(app)
    include_all_routers(app, settings)

    return app
