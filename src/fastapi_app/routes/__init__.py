from fastapi import APIRouter, FastAPI

from ..settings.config import Settings
from .admin_internal import router as admin_internal_router
from .health import router as health_router
from .items import router as items_router


def include_all_routers(app: FastAPI, settings: Settings):
    api = APIRouter(prefix=settings.api_prefix)
    api.include_router(health_router, tags=["health"])
    api.include_router(items_router, tags=["items"])
    api.include_router(admin_internal_router, tags=["internal"])
    app.include_router(api)
