from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from src.domain.example.entities.example_entity import ExampleEntity
from src.domain.example.repositories.example_repository import ExampleRepository
from src.domain.example.value_objects.example_id import ExampleId


@dataclass
class LoadExampleService:
    """Сервис для загрузки примеров. Query в CQRS."""
    repository: ExampleRepository

    def by_id(self, example_id: str) -> Optional[ExampleEntity]:
        """Загрузить сущность по ID"""
        return self.repository.get_by_id(ExampleId(example_id))

    def latest(self) -> Optional[ExampleEntity]:
        """Загрузить последнюю сущность"""
        return self.repository.get_latest()

