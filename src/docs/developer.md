Документация для разработчиков

ВАЖНО!
Проект использует in-memory хранилище и не требует внешних зависимостей для базовой функциональности.

Именования и соглашения

В коде используется соглашение:

Префикс	Назначение
get_	получение данных из БД
fetch_	получение данных из сети
load_	получение данных из сети и сохранение в БД

Архитектура следует принципам DDD + CQRS.
Query — операции чтения (GET).
Command — операции изменения состояния (POST, PUT, DELETE).
Handler — обработчики команд/запросов.
Event — доменные события.
Bus — шина событий или команд.

Типы данных:

Слой	Типы
Контроллер	DTO (pydantic) — валидация, документация, приём данных
Сервис / Use-case	бизнес-логика, сущности, value-objects
Хранение	Entity, репозитории (in-memory хранилище)
Ответ клиенту	Response DTO — фильтрует и форматирует результат

Структура проекта (DDD)
src/
├── domain/                    # чистые бизнес-сущности, value-objects, интерфейсы репозиториев
│   └── example/
│       ├── entities/          # Сущности
│       ├── repositories/      # Интерфейсы репозиториев
│       └── value_objects/     # Объекты-значения
├── application/               # use-cases (commands, queries, handlers)
│   └── example/
│       ├── commands/          # Команды (изменение состояния)
│       └── queries/           # Запросы (чтение данных)
├── infrastructure/            # реализации репозиториев, внешние клиенты, базы данных
│   └── example/
│       ├── repositories/      # Реализации репозиториев
│       └── db/               # Хранилище данных
├── presentation/              # HTTP-контроллеры, схемы DTO, FastAPI endpoints
│   └── http/
│       └── example/
│           ├── dto/          # DTO для API
│           ├── example_controller.py
│           └── example_module.py
└── main.py                   # bootstrap приложения

Пример слоя presentation
# src/presentation/http/example/example_controller.py
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
    router = APIRouter(prefix="/example", tags=["example"])

    @router.post("", status_code=status.HTTP_201_CREATED)
    def save_example(dto: ExampleRequestDTO) -> None:
        save_service.execute(example_id=dto.id, content=dto.content)

    @router.get("", response_model=ExampleResponseDTO)
    def get_example() -> ExampleResponseDTO:
        entity = get_service.execute()
        if entity is None:
            return ExampleResponseDTO(id="", content="")
        return ExampleResponseDTO(id=str(entity.example_id), content=entity.content)

    return router

Пример слоя application
# src/application/example/commands/save_example_service.py
from dataclasses import dataclass
from src.domain.example.entities.example_entity import ExampleEntity
from src.domain.example.repositories.example_repository import ExampleRepository
from src.domain.example.value_objects.example_id import ExampleId

@dataclass
class SaveExampleService:
    repository: ExampleRepository

    def execute(self, example_id: str, content: str) -> None:
        entity = ExampleEntity(example_id=ExampleId(example_id), content=content)
        self.repository.save(entity)

Пример слоя domain
# src/domain/example/entities/example_entity.py
from dataclasses import dataclass
from src.domain.example.value_objects.example_id import ExampleId

@dataclass
class ExampleEntity:
    example_id: ExampleId
    content: str

    def __post_init__(self) -> None:
        if not isinstance(self.content, str) or self.content.strip() == "":
            raise ValueError("content must be a non-empty string")

# src/domain/example/repositories/example_repository.py
from typing import Protocol, Optional, List
from src.domain.example.entities.example_entity import ExampleEntity
from src.domain.example.value_objects.example_id import ExampleId

class ExampleRepository(Protocol):
    def save(self, entity: ExampleEntity) -> None: ...
    def get_by_id(self, example_id: ExampleId) -> Optional[ExampleEntity]: ...
    def get_latest(self) -> Optional[ExampleEntity]: ...
    def list_all(self) -> List[ExampleEntity]: ...

Пример слоя infrastructure
# src/infrastructure/example/repositories/example_repository_impl.py
from src.domain.example.entities.example_entity import ExampleEntity
from src.domain.example.repositories.example_repository import ExampleRepository
from src.domain.example.value_objects.example_id import ExampleId
from src.infrastructure.example.db.memory_storage import InMemoryExampleStorage

class InMemoryExampleRepository(ExampleRepository):
    def __init__(self, storage: InMemoryExampleStorage) -> None:
        self._storage = storage

    def save(self, entity: ExampleEntity) -> None:
        self._storage.save(entity)

main.py
from fastapi import FastAPI
from src.presentation.http.example.example_module import build_example_router

app = FastAPI(title="DDD FastAPI Example", version="0.1.0")
app.include_router(build_example_router())

@app.get("/health")
def health() -> dict:
    return {"status": "ok"}

Конфигурация

Проект не требует внешних конфигурационных файлов. Все настройки по умолчанию:
- Порт: 8000
- Хранилище: in-memory
- Автоперезагрузка: включена в режиме разработки

Отступы — четыре пробела (стандарт Python).

Запуск
Локально
```bash
pip install -r requirements.txt
uvicorn src.main:app --reload
```

В Docker (опционально)
```dockerfile
FROM python:3.10-alpine

WORKDIR /app
COPY requirements.txt ./
RUN pip install -r requirements.txt
COPY src ./src
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Тестирование
```bash
pytest -v
```

Тесты по слоям:

- unit: domain, application (mock репозиториев)
- integration: infrastructure (in-memory хранилище)
- api: presentation (FastAPI test client)

Контрибьюция и кодстайл

- Black + isort — форматирование
- mypy — статическая проверка
- pre-commit hooks обязательны
- Тесты должны быть зелёные перед merge

TODO

- добавить примеры CQRS (CommandHandler, QueryHandler)
- добавить интеграцию с Redis и SQLAlchemy
- описать миграции Alembic
- добавить CI (GitHub Actions)
- добавить валидацию в DTO
- добавить обработку ошибок
