import logging

from fastapi import APIRouter, Depends

# Используем Django ORM
from apps.core.models import Item

from ..core.deps import pagination_params
from ..schemas.items import ItemOut

logger = logging.getLogger("logger")

router = APIRouter()


@router.get("/items", response_model=list[ItemOut])
def list_items(p: tuple[int, int] = Depends(pagination_params)):
    limit, offset = p
    qs = Item.objects.order_by("-created_at")[offset: offset + limit]
    return [ItemOut.model_validate(obj) for obj in qs]
