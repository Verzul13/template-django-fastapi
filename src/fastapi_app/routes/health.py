import logging

from fastapi import APIRouter

router = APIRouter()

logger = logging.getLogger("logger")


@router.get("/health")
def health():
    return {"status": "ok", "app": "fastapi"}
