from __future__ import annotations

from fastapi import APIRouter, status
from typing import List

from src.application.users.queries.get_users_by_ids import GetUsersByIdsHandler
from src.presentation.http.users.dto.user_dto import (
    UsersBatchRequestDTO,
    UserDTO,
)


def create_users_router(
    handler: GetUsersByIdsHandler,
) -> APIRouter:
    """
    Создать роутер для работы с пользователями.

    Основная ручка:
    - POST /users/batch — получить данные пользователей по списку ID.
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

    return router


