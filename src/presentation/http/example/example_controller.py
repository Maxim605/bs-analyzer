from __future__ import annotations

from fastapi import APIRouter, status

from src.application.example.commands.save_example_service import SaveExampleService
from src.application.example.queries.get_example_service import GetExampleService
from src.presentation.http.example.dto.example_1_dto import (
    ExampleRequestDTO,
    ExampleResponseDTO,
)


def create_example_router(
    save_service: SaveExampleService,
    get_service: GetExampleService,
) -> APIRouter:
    """Создать роутер для примеров с ручной инъекцией зависимостей"""
    router = APIRouter(prefix="/example", tags=["example"])

    @router.post("", status_code=status.HTTP_201_CREATED)
    def save_example(dto: ExampleRequestDTO) -> None:
        """POST /example - Сохранить пример через SaveExampleService"""
        save_service.execute(example_id=dto.id, content=dto.content)

    @router.get("", response_model=ExampleResponseDTO)
    def get_example() -> ExampleResponseDTO:
        """GET /example - Получить последний пример через GetExampleService"""
        entity = get_service.execute()
        if entity is None:
            return ExampleResponseDTO(id="", content="")
        return ExampleResponseDTO(id=str(entity.example_id), content=entity.content)

    return router

