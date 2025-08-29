# src/fastapi_app/asyncdb/auto.py

import hashlib
import inspect
from collections import Counter
from dataclasses import dataclass
from typing import Optional

from django.apps import apps as django_apps
from django.db.models import Model
from sqlalchemy import MetaData
from sqlalchemy import inspect as sa_inspect
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy.ext.automap import automap_base

from ..core.django_init import ensure_django_initialized
from .engine import engine


def snake_to_pascal(s: str) -> str:
    return "".join(p.capitalize() for p in s.split("_") if p)


@dataclass
class MappingState:
    migration_sig: str = ""
    Base = None
    metadata: Optional[MetaData] = None
    class_by_table: dict[str, str] = None  # db_table -> SA class name


state = MappingState(class_by_table={})


async def _calc_migration_signature(conn: AsyncConnection) -> str:
    rows = (await conn.execute(text(
        "SELECT app, name FROM django_migrations ORDER BY app, name"
    ))).all()
    digest = hashlib.sha256()
    for app, name in rows:
        digest.update(app.encode("utf-8") + b":" + name.encode("utf-8") + b";")
    return digest.hexdigest()


def _build_table_allowlist() -> set[str]:
    allow: set[str] = set()
    for model in django_apps.get_models():
        allow.add(model._meta.db_table)
        for m2m in model._meta.many_to_many:
            try:
                t = m2m.m2m_db_table()
                if t:
                    allow.add(t)
            except Exception:
                pass
    return allow


def _classname_for_table(base, tablename: str, table):
    return state.class_by_table.get(tablename, snake_to_pascal(tablename))


def _name_for_scalar_relationship(base, local_cls, referred_cls, constraint):
    return referred_cls.__name__.lower()


def _name_for_collection_relationship(base, local_cls, referred_cls, constraint):
    return f"{referred_cls.__name__.lower()}_set"


async def refresh_mapping(force: bool = False) -> None:
    """
    Безопасно пересобирает automap:
    - Считает сигнатуру миграций
    - Строит устойчивые имена SA-классов: ModelName или AppLabel+ModelName при коллизиях
    - Reflect делает ТОЛЬКО по реально существующим таблицам (чтобы не падать до миграций)
    """
    ensure_django_initialized("django_project.settings")

    async with engine.begin() as conn:
        sig = await _calc_migration_signature(conn)
        if not force and sig == state.migration_sig and state.Base is not None:
            return

        # 1) Карта db_table -> имя SA-класса (устойчивые имена)
        django_models = list(django_apps.get_models())
        counts = Counter(m.__name__ for m in django_models)

        class_by_table: dict[str, str] = {}
        for m in django_models:
            db_table = m._meta.db_table
            model_name = m.__name__
            if counts[model_name] == 1:
                sa_name = model_name
            else:
                sa_name = f"{m._meta.app_label.capitalize()}{model_name}"
            class_by_table[db_table] = sa_name

        # 2) Allowlist (по моделям и m2m), но отражаем только существующие таблицы
        allow = _build_table_allowlist()

        def _existing_tables(sync_conn):
            insp = sa_inspect(sync_conn)
            # NOTE: ограничиваемся default schema (public); добавь schema_name при необходимости
            return set(insp.get_table_names(schema=None))

        existing = await conn.run_sync(_existing_tables)
        to_reflect = allow & existing

        if not to_reflect:
            # Нечего отражать сейчас — видимо, миграции ещё не накатывались.
            # Просто обновим сигнатуру и карту имён; watcher/сигнал подтянут после migrate.
            state.migration_sig = sig
            state.class_by_table = class_by_table
            state.Base = automap_base(metadata=MetaData())  # пустая база, но валидная
            state.metadata = state.Base.metadata
            return

        md = MetaData()
        # reflect только существующие
        await conn.run_sync(md.reflect, only=to_reflect)

        Base = automap_base(metadata=md)

        def _prepare(sync_conn):
            Base.prepare(
                autoload_with=sync_conn,
                classname_for_table=_classname_for_table,
                name_for_scalar_relationship=_name_for_scalar_relationship,
                name_for_collection_relationship=_name_for_collection_relationship,
            )

        # сделаем карту видимой для _classname_for_table
        state.class_by_table = class_by_table
        await conn.run_sync(_prepare)

        # зафиксировать состояние
        state.Base = Base
        state.metadata = md
        state.migration_sig = sig


def get_mapped_class(target):
    """
    Возвращает SQLAlchemy-класс из automap:
      - Django класс: get_mapped_class(AppsCoreItem)
      - "ModelName": если имя уникально среди всех apps
      - "app_label.ModelName": точное указание
    """
    if state.Base is None:
        raise RuntimeError("AutoMap is not initialized. Call refresh_mapping() first.")

    # 1) Django класс — самый надёжный путь
    if inspect.isclass(target) and issubclass(target, Model):
        db_table = target._meta.db_table
        sa_name = state.class_by_table[db_table]  # имя класса, которое мы зафиксировали в refresh_mapping
        return getattr(state.Base.classes, sa_name)

    # 2) Строки
    if isinstance(target, str):
        name = target.strip()

        # "app_label.ModelName"
        if "." in name:
            app_label, model_name = name.split(".", 1)
            m = django_apps.get_model(app_label, model_name)
            if m is None:
                raise KeyError(f"Django model '{name}' not found")
            db_table = m._meta.db_table
            sa_name = state.class_by_table[db_table]
            return getattr(state.Base.classes, sa_name)

        # просто "ModelName" — проверим уникальность
        matches = [m for m in django_apps.get_models() if m.__name__ == name]
        if not matches:
            raise KeyError(f"Django model '{name}' not found")
        if len(matches) > 1:
            apps_list = ", ".join(sorted({m._meta.app_label for m in matches}))
            raise ValueError(
                f"Model name '{name}' is ambiguous across apps: {apps_list}. "
                f"Use 'app_label.{name}' instead."
            )
        m = matches[0]
        db_table = m._meta.db_table
        sa_name = state.class_by_table[db_table]
        return getattr(state.Base.classes, sa_name)

    raise TypeError(f"Unsupported target type: {type(target)}")
