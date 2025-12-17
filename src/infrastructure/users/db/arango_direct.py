"""
Прямое подключение к ArangoDB (fallback, если Thrift сервер не доступен).

Использует python-arango для прямого подключения к БД.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from dataclasses import dataclass, field

from src.infrastructure.config import config

try:
    from arango import ArangoClient
    ARANGO_AVAILABLE = True
except ImportError:
    ARANGO_AVAILABLE = False
    ArangoClient = None


@dataclass
class ArangoDirectClient:
    """
    Прямой клиент для работы с ArangoDB.
    
    Используется как fallback, если Thrift сервер не доступен.
    """
    
    hosts: str = field(default_factory=lambda: config.ARANGO_URL)
    username: str = field(default_factory=lambda: config.ARANGO_USERNAME)
    password: str = field(default_factory=lambda: config.ARANGO_PASSWORD)
    database: str = field(default_factory=lambda: config.ARANGO_DATABASE)
    _client: Any = field(default=None, init=False, repr=False)
    _db: Any = field(default=None, init=False, repr=False)
    
    def _ensure_connection(self):
        """Установить соединение с ArangoDB."""
        if not ARANGO_AVAILABLE:
            raise ImportError(
                "python-arango not installed. Install with: pip install python-arango"
            )
        
        if self._db is None:
            try:
                self._client = ArangoClient(hosts=self.hosts)
                self._db = self._client.db(
                    name=self.database,
                    username=self.username,
                    password=self.password
                )
            except Exception as e:
                raise ConnectionError(f"Failed to connect to ArangoDB: {e}")
    
    def get(self, collection: str, key: str) -> Dict[str, Any]:
        """
        Получить документ из ArangoDB.
        
        Args:
            collection: Имя коллекции
            key: Ключ документа
            
        Returns:
            Словарь с результатом: {'fields': dict, 'error': str}
        """
        self._ensure_connection()
        
        try:
            col = self._db.collection(collection)
            doc = col.get(key)
            
            # Преобразуем документ в формат, совместимый с Thrift ответом
            # Все значения должны быть строками (как в Thrift)
            fields: Dict[str, str] = {}
            for k, v in doc.items():
                if k != '_id' and k != '_key' and k != '_rev':  # Исключаем служебные поля
                    fields[k] = str(v) if v is not None else ""
            
            return {
                'fields': fields,
                'error': None
            }
        except Exception as e:
            error_msg = str(e)
            # Если документ не найден, это не критическая ошибка
            if "not found" in error_msg.lower() or "404" in error_msg:
                return {
                    'fields': None,
                    'error': f"Document not found: {key}"
                }
            return {
                'fields': None,
                'error': error_msg
            }
    
    def close(self):
        """Закрыть соединение."""
        self._db = None
        self._client = None
    
    def __enter__(self):
        """Контекстный менеджер."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Закрытие при выходе из контекста."""
        self.close()

