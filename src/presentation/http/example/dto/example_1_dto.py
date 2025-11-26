from __future__ import annotations

from pydantic import BaseModel, Field


class ExampleRequestDTO(BaseModel):
    """DTO для запроса создания примера"""
    id: str = Field(..., description="Уникальный идентификатор примера")
    content: str = Field(..., description="Содержимое примера")


class ExampleResponseDTO(BaseModel):
    """DTO для ответа с данными примера"""
    id: str
    content: str

