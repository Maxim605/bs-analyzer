from __future__ import annotations

from fastapi import APIRouter

from src.infrastructure.users.db.users_db import UsersDb
from src.application.users.queries.get_users_by_ids import GetUsersByIdsHandler
from src.application.users.queries.get_users_metrics import GetUsersMetricsHandler
from src.presentation.http.users.users_controller import create_users_router


def build_users_module() -> APIRouter:
    """
    Сборка модуля Users (Composition Root).

    Здесь настраиваются зависимости и создается FastAPI-роутер.
    """
    # 1. Infrastructure
    users_db = UsersDb()

    # 2. Application
    handler = GetUsersByIdsHandler(db=users_db)
    metrics_handler = GetUsersMetricsHandler(db=users_db)

    # 3. Presentation
    router = create_users_router(handler, metrics_handler)
    return router


