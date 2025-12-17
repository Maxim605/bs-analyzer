"""
Модуль для работы с конфигурацией из .env файла.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Загружаем .env файл из корня проекта
project_root = Path(__file__).parent.parent.parent
env_file = project_root / ".env"
if env_file.exists():
    load_dotenv(env_file)


class Config:
    """Класс для работы с конфигурацией из .env."""
    
    # Порт приложения
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # Thrift настройки
    THRIFT_HOST: str = os.getenv("THRIFT_HOST", "localhost")
    THRIFT_PORT: int = int(os.getenv("THRIFT_PORT", "9090"))
    
    # ArangoDB настройки
    ARANGO_URL: str = os.getenv("ARANGO_URL", "http://localhost:8529")
    ARANGO_DATABASE: str = os.getenv("ARANGO_DATABASE", "_system")
    ARANGO_USERNAME: str = os.getenv("ARANGO_USERNAME", "root")
    ARANGO_PASSWORD: str = os.getenv("ARANGO_PASSWORD", "")
    
    # Users collection
    USERS_COLLECTION: str = os.getenv("USERS_COLLECTION", "users")
    
    # Batch size
    BATCH_SIZE: int = int(os.getenv("BATCH_SIZE", "100"))


# Глобальный экземпляр конфигурации
config = Config()

