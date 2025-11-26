from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional, List

from src.domain.example.entities.example_entity import ExampleEntity
from src.domain.example.value_objects.example_id import ExampleId


@dataclass
class InMemoryExampleStorage:
    """In-memory хранилище для примеров. Данные теряются при перезапуске."""
    items: Dict[str, ExampleEntity] = field(default_factory=dict)
    last_key: Optional[str] = None

    def save(self, entity: ExampleEntity) -> None:
        """Сохранить сущность в памяти"""
        key = str(entity.example_id)
        self.items[key] = entity
        self.last_key = key

    def get_by_id(self, example_id: ExampleId) -> Optional[ExampleEntity]:
        """Получить сущность по ID из памяти"""
        return self.items.get(str(example_id))

    def get_latest(self) -> Optional[ExampleEntity]:
        """Получить последнюю сохранённую сущность"""
        if self.last_key is None:
            return None
        return self.items.get(self.last_key)

    def list_all(self) -> List[ExampleEntity]:
        """Получить все сущности из памяти"""
        return list(self.items.values())

