from __future__ import annotations

from dataclasses import dataclass

from src.domain.example.value_objects.example_id import ExampleId


@dataclass
class ExampleEntity:
    """Доменная сущность примера. Содержит бизнес-логику и валидацию."""
    example_id: ExampleId
    content: str

    def __post_init__(self) -> None:
        if not isinstance(self.content, str) or self.content.strip() == "":
            raise ValueError("content must be a non-empty string")

