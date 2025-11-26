## Быстрый старт

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 2. Запуск сервера

```bash
uvicorn src.main:app --reload
```

### 3. Проверка работы

- **Swagger документация**: http://localhost:8000/docs
- **Проверка здоровья**: http://localhost:8000/health
- **API endpoints**:
  - `POST /example` - Сохранить пример
  - `GET /example` - Получить последний пример

## Тестирование API

### Способ 1: Swagger UI (рекомендуется)
Откройте http://localhost:8000/docs и используйте интерактивный интерфейс

### Способ 2: PowerShell команды
```powershell
# Сохранить пример
Invoke-RestMethod -Uri "http://localhost:8000/example" -Method POST -ContentType "application/json" -Body '{"id": "123", "content": "Hello world!"}'

# Получить пример
Invoke-RestMethod -Uri "http://localhost:8000/example" -Method GET

# Проверка здоровья
Invoke-RestMethod -Uri "http://localhost:8000/health" -Method GET
```

### Способ 3: curl (Linux/Mac)
```bash
# Сохранить пример
curl -X POST http://localhost:8000/example -H "Content-Type: application/json" -d '{"id": "123", "content": "Hello world!"}'

# Получить пример
curl http://localhost:8000/example

# Проверка здоровья
curl http://localhost:8000/health
```

## Зависимости

- `fastapi` - веб-фреймворк
- `uvicorn` - ASGI сервер
- `pydantic` - валидация данных


## Документация

- [Административная документация](src/docs/adm.md)
- [Документация для разработчиков](src/docs/developer.md)
