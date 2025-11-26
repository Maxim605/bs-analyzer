from __future__ import annotations

from src.application.example.commands.save_example_service import SaveExampleService
from src.application.example.queries.get_example_service import GetExampleService
from src.infrastructure.example.db.memory_storage import InMemoryExampleStorage
from src.infrastructure.example.repositories.example_repository_impl import (
    InMemoryExampleRepository,
)
from src.presentation.http.example.example_controller import create_example_router


def build_example_router():
    """Сборка роутера с ручной инъекцией зависимостей (простая DI)"""
    storage = InMemoryExampleStorage()
    repository = InMemoryExampleRepository(storage=storage)
    save_service = SaveExampleService(repository=repository)
    get_service = GetExampleService(repository=repository)

    return create_example_router(save_service=save_service, get_service=get_service)

