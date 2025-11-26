from __future__ import annotations

from typing import Optional, List

from src.domain.example.entities.example_entity import ExampleEntity
from src.domain.example.repositories.example_repository import ExampleRepository
from src.domain.example.value_objects.example_id import ExampleId
from src.infrastructure.example.db.memory_storage import InMemoryExampleStorage


class InMemoryExampleRepository(ExampleRepository):
    """Реализация репозитория с in-memory хранилищем."""
    def __init__(self, storage: InMemoryExampleStorage) -> None:
        self._storage = storage

    def save(self, entity: ExampleEntity) -> None:
        """Сохранить сущность через хранилище"""
        self._storage.save(entity)

    def get_by_id(self, example_id: ExampleId) -> Optional[ExampleEntity]:
        """Получить сущность по ID через хранилище"""
        return self._storage.get_by_id(example_id)

    def get_latest(self) -> Optional[ExampleEntity]:
        """Получить последнюю сущность через хранилище"""
        return self._storage.get_latest()

    def list_all(self) -> List[ExampleEntity]:
        """Получить все сущности через хранилище"""
        return self._storage.list_all()

