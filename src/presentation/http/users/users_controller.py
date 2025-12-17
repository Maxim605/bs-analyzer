from __future__ import annotations

from fastapi import APIRouter, status
from typing import List

from src.application.users.queries.get_users_by_ids import GetUsersByIdsHandler
from src.application.users.queries.get_users_metrics import GetUsersMetricsHandler
from src.presentation.http.users.dto.user_dto import (
    UsersBatchRequestDTO,
    UserDTO,
    UsersMetricsRequestDTO,
    UsersMetricsResponseDTO,
)


def create_users_router(
    handler: GetUsersByIdsHandler,
    metrics_handler: GetUsersMetricsHandler,
) -> APIRouter:
    """
    Создать роутер для работы с пользователями.

    Ручки:
    - POST /users/batch — получить данные пользователей по списку ID.
    - POST /users/metrics — рассчитать метрики по данным пользователей.
    """

    router = APIRouter(prefix="/users", tags=["users"])

    @router.post(
        "/batch",
        response_model=List[UserDTO],
        status_code=status.HTTP_200_OK,
        summary="Получить пользователей по списку ID батчами",
    )
    async def get_users_batch(dto: UsersBatchRequestDTO) -> List[UserDTO]:
        """
        Получить данные пользователей по списку ID.

        Внутри обработчик дергает ArangoDB батчами.
        """
        raw_results = await handler.execute(dto.ids)

        return [
            UserDTO(id=item["id"], data=item.get("fields"), error=item.get("error"))
            for item in raw_results
        ]

    @router.post(
        "/metrics",
        response_model=UsersMetricsResponseDTO,
        status_code=status.HTTP_200_OK,
        summary="Рассчитать метрики по данным пользователей",
    )
    async def get_users_metrics(dto: UsersMetricsRequestDTO) -> UsersMetricsResponseDTO:
        """
        Рассчитать метрики по данным пользователей.

        Параметры:
        - ids: список ID пользователей
        - numeric_fields: числовые поля для анализа (среднее, медиана, дисперсия)
        - categorical_fields: категориальные поля для анализа (распределение)
        - fillna_mean: заполнять пустые значения средним (для числовых)
        - fillna: значение для заполнения пустот (для категориальных)
        """
        result = await metrics_handler.execute(
            user_ids=dto.ids,
            numeric_fields=dto.numeric_fields,
            categorical_fields=dto.categorical_fields,
            fillna_mean=dto.fillna_mean,
            fillna=dto.fillna,
        )

        return UsersMetricsResponseDTO(**result)

    return router


