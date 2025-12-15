## Быстрый старт

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 2. Настройка конфигурации

Создайте файл `.env` в корне проекта со следующими параметрами:

```env
PORT=8000
THRIFT_HOST=localhost
THRIFT_PORT=9090
ARANGO_URL=http://localhost:8529
ARANGO_DATABASE=bs
ARANGO_USERNAME=root
ARANGO_PASSWORD=
USERS_COLLECTION=users
BATCH_SIZE=100
```

### 3. Запуск сервера

**Windows (PowerShell):**
```powershell
.\start.ps1
```

**Или напрямую:**
```bash
uvicorn src.main:app --reload --port 8000
```

Порт можно изменить в файле `.env` (переменная `PORT`).

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
- `python-dotenv` - загрузка конфигурации из .env
- `thriftpy2` - Thrift клиент для работы с ArangoDB
- `python-arango` - прямой клиент для работы с ArangoDB


## Документация

- [Административная документация](src/docs/adm.md)
- [Документация для разработчиков](src/docs/developer.md)
