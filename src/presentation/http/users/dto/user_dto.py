from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class UsersBatchRequestDTO(BaseModel):
    """Запрос на получение данных пользователей по списку ID."""

    ids: List[str] = Field(..., description="Список идентификаторов пользователей")


class UserDTO(BaseModel):
    """Данные одного пользователя из ArangoDB."""

    id: str = Field(..., description="Идентификатор пользователя")
    data: Optional[Dict[str, str]] = Field(
        None, description="Поля документа пользователя из ArangoDB"
    )
    error: Optional[str] = Field(
        None, description="Описание ошибки при получении пользователя, если была"
    )


