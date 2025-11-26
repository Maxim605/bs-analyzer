from __future__ import annotations

from typing import Protocol, Optional, List

from src.domain.example.entities.example_entity import ExampleEntity
from src.domain.example.value_objects.example_id import ExampleId


class ExampleRepository(Protocol):
    """Интерфейс репозитория для работы с примерами. Определяет контракт хранения."""
    def save(self, entity: ExampleEntity) -> None:
        """Сохранить сущность"""
        ...

    def get_by_id(self, example_id: ExampleId) -> Optional[ExampleEntity]:
        """Получить сущность по ID"""
        ...

    def get_latest(self) -> Optional[ExampleEntity]:
        """Получить последнюю сохранённую сущность"""
        ...

    def list_all(self) -> List[ExampleEntity]:
        """Получить все сущности"""
        ...

