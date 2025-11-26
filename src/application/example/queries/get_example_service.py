from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from src.domain.example.entities.example_entity import ExampleEntity
from src.domain.example.repositories.example_repository import ExampleRepository


@dataclass
class GetExampleService:
    """Сервис для получения последнего примера. Query в CQRS."""
    repository: ExampleRepository

    def execute(self) -> Optional[ExampleEntity]:
        """Получить последнюю сохранённую сущность"""
        return self.repository.get_latest()

