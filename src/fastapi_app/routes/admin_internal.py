# src/fastapi_app/routes/admin_internal.py
import os

from fastapi import APIRouter, Header, HTTPException

from ..asyncdb.auto import refresh_mapping

router = APIRouter()

INTERNAL_TOKEN = os.getenv("FASTAPI_REFRESH_TOKEN", "")


@router.post("/_internal/refresh-mapping")
async def internal_refresh_mapping(x_internal_token: str = Header(default="")):
    """ Эндпоинт для после применения миграций на Django """
    if not INTERNAL_TOKEN or x_internal_token != INTERNAL_TOKEN:
        raise HTTPException(status_code=403, detail="Forbidden")
    await refresh_mapping(force=True)
    return {"status": "refreshed"}
