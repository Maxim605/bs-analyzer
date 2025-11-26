---
title: Документация
---

\newpage

# Общие сведения

Программа представляет собой веб-сервис, реализованный на Python (FastAPI) с использованием архитектуры DDD (Domain-Driven Design) и паттерна CQRS.  
Приложение использует in-memory хранилище и не требует внешних зависимостей для базовой функциональности.

Exposed порт: `8000`.  
Основной процесс — веб-сервер Uvicorn (`uvicorn src.main:app`).

---

# Структура программы

## Дистрибутив

* Python 3.10+
* Менеджер пакетов: `pip`
* Код в каталоге `src/`
* Точка входа: `src/main.py`
* Команда запуска:  
  ```bash
  uvicorn src.main:app --reload
  ```

## Структура проекта (DDD)

```
src/
├── domain/                    # Доменный слой
│   └── example/
│       ├── entities/          # Сущности
│       │   └── example_entity.py
│       ├── repositories/      # Интерфейсы репозиториев
│       │   └── example_repository.py
│       └── value_objects/     # Объекты-значения
│           └── example_id.py
├── application/               # Слой приложения
│   └── example/
│       ├── commands/          # Команды (изменение состояния)
│       │   ├── save_example_service.py
│       │   └── load_example_service.py
│       └── queries/           # Запросы (чтение данных)
│           ├── get_example_service.py
│           └── fetch_example_service.py
├── infrastructure/            # Инфраструктурный слой
│   └── example/
│       ├── repositories/      # Реализации репозиториев
│       │   └── example_repository_impl.py
│       └── db/               # Хранилище данных
│           └── memory_storage.py
├── presentation/             # Слой представления
│   └── http/
│       └── example/
│           ├── dto/          # DTO для API
│           │   └── example_1_dto.py
│           ├── example_controller.py
│           └── example_module.py
└── main.py                   # Точка входа приложения
```

## API Endpoints

* `POST /example` - Сохранить пример (id, content)
* `GET /example` - Получить последний сохранённый пример
* `GET /health` - Проверка состояния сервиса
* `GET /docs` - Swagger документация

## Зависимости

```
fastapi
uvicorn
pydantic
