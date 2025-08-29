import logging

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, join, select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.core.models import (Category, Item, ItemTag, Order, OrderItem,
                              Supplier, Tag)

from ..asyncdb.auto import get_mapped_class, state
from ..asyncdb.engine import get_async_session

logger = logging.getLogger("logger")

router = APIRouter()


# 1) Простой список items (SELECT ... FROM core_item)
@router.get("/demo/items")
async def demo_items(
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_async_session),
):
    SAItem = get_mapped_class(Item)
    stmt = (
        select(SAItem.id, SAItem.name, SAItem.created_at)
        .order_by(SAItem.created_at.desc())
        .limit(limit).offset(offset)
    )
    rows = (await session.execute(stmt)).mappings().all()
    return [dict(r) for r in rows]


# 2) JOIN: items + supplier (FK)
@router.get("/demo/items_with_supplier")
async def demo_items_with_supplier(
    limit: int = 20,
    session: AsyncSession = Depends(get_async_session),
):
    SAItem = get_mapped_class(Item)
    SASupplier = get_mapped_class(Supplier)

    j = join(SAItem, SASupplier, SAItem.supplier_id == SASupplier.id)
    stmt = select(
        SAItem.id.label("item_id"),
        SAItem.name.label("item_name"),
        SASupplier.name.label("supplier"),
    ).select_from(j).limit(limit)

    rows = (await session.execute(stmt)).mappings().all()
    return [dict(r) for r in rows]


# 3) M2M (авто-таблица через ManyToManyField): items + categories
@router.get("/demo/items_categories")
async def demo_items_categories(
    limit: int = 50,
    session: AsyncSession = Depends(get_async_session),
):
    SAItem = get_mapped_class(Item)
    SACategory = get_mapped_class(Category)

    # automap создаёт secondary таблицу с именем типа core_item_categories (зависит от Django)
    # безопаснее сделать manual join через реальную m2m таблицу имени:
    # Django автогенерит <app>_<model>_<field> например: core_item_categories
    # Узнать имя можно так:
    m2m_table_name = Item._meta.get_field("categories").m2m_db_table()
    # достаём secondary как Table из metadata
    secondary = state.metadata.tables[m2m_table_name]

    j = (SAItem.__table__
         .join(secondary, SAItem.id == secondary.c.item_id)
         .join(SACategory.__table__, SACategory.id == secondary.c.category_id))

    stmt = select(
        SAItem.id.label("item_id"),
        SAItem.name.label("item_name"),
        SACategory.id.label("category_id"),
        SACategory.title.label("category"),
    ).select_from(j).limit(limit)

    rows = (await session.execute(stmt)).mappings().all()
    return [dict(r) for r in rows]


# 4) M2M через кастомный through (ItemTag + extra field 'weight')
@router.get("/demo/items_tags")
async def demo_items_tags(
    limit: int = 50,
    session: AsyncSession = Depends(get_async_session),
):
    SAItem = get_mapped_class(Item)
    SATag = get_mapped_class(Tag)
    SAItemTag = get_mapped_class(ItemTag)

    j = (SAItem.__table__
         .join(SAItemTag.__table__, SAItem.id == SAItemTag.item_id)
         .join(SATag.__table__, SATag.id == SAItemTag.tag_id))

    stmt = select(
        SAItem.id.label("item_id"),
        SAItem.name.label("item_name"),
        SATag.id.label("tag_id"),
        SATag.title.label("tag"),
        SAItemTag.weight,
    ).select_from(j).limit(limit)

    rows = (await session.execute(stmt)).mappings().all()
    return [dict(r) for r in rows]


# 5) Агрегация: число позиций в заказе по пользователю
@router.get("/demo/orders_stats/{user_id}")
async def demo_orders_stats(
    user_id: int,
    session: AsyncSession = Depends(get_async_session),
):
    SAOrder = get_mapped_class(Order)
    SAOrderItem = get_mapped_class(OrderItem)
    # count(order_items) по всем заказам пользователя
    j = join(SAOrder, SAOrderItem, SAOrder.id == SAOrderItem.order_id)
    total = (await session.execute(
        select(func.count()).select_from(j).where(SAOrder.user_id == user_id)
    )).scalar_one()
    return {"user_id": user_id, "order_items_count": total}
