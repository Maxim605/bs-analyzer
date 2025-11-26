from __future__ import annotations

from dataclasses import dataclass
from typing import List

from src.domain.example.entities.example_entity import ExampleEntity
from src.domain.example.repositories.example_repository import ExampleRepository


@dataclass
class FetchExampleService:
    """Сервис для получения всех примеров. Query в CQRS."""
    repository: ExampleRepository

    def execute(self) -> List[ExampleEntity]:
        """Получить все сохранённые сущности"""
        return self.repository.list_all()

