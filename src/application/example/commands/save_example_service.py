from __future__ import annotations

from dataclasses import dataclass

from src.domain.example.entities.example_entity import ExampleEntity
from src.domain.example.repositories.example_repository import ExampleRepository
from src.domain.example.value_objects.example_id import ExampleId


@dataclass
class SaveExampleService:
    """Сервис для сохранения примера. Command в CQRS."""
    repository: ExampleRepository

    def execute(self, example_id: str, content: str) -> None:
        """Создать и сохранить сущность примера"""
        entity = ExampleEntity(example_id=ExampleId(example_id), content=content)
        self.repository.save(entity)

