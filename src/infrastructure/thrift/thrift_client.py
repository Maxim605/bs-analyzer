"""
Thrift-клиент для подключения к ArangoDB через Thrift.

Аналог TypeScript версии из thrift/thrift-arango.service.ts
"""

from __future__ import annotations

from typing import Any, Dict
from dataclasses import dataclass, field
from pathlib import Path

from src.infrastructure.config import config

try:
    import thriftpy2
    from thriftpy2.rpc import make_client
    from thriftpy2.protocol import TBinaryProtocolFactory
    from thriftpy2.transport import TBufferedTransportFactory
    THRIFT_AVAILABLE = True
except ImportError:
    THRIFT_AVAILABLE = False
    thriftpy2 = None


@dataclass
class ThriftArangoClient:
    """
    Thrift-клиент для работы с ArangoDB.
    
    Аналог TypeScript версии ThriftArangoService.
    """
    
    host: str = field(default_factory=lambda: config.THRIFT_HOST)
    port: int = field(default_factory=lambda: config.THRIFT_PORT)
    _client: Any = field(default=None, init=False, repr=False)
    _transport: Any = field(default=None, init=False, repr=False)
    
    def _ensure_connection(self):
        """Установить соединение с Thrift сервером."""
        if not THRIFT_AVAILABLE:
            raise ImportError(
                "thriftpy2 not installed. Install with: pip install thriftpy2"
            )
        
        if self._client is None:
            try:
                # Используем динамическую загрузку thrift файла
                # Файл находится в корне проекта в папке thrift
                project_root = Path(__file__).parent.parent.parent.parent
                thrift_file = project_root / "thrift" / "arango.thrift"
                
                if not thrift_file.exists():
                    raise FileNotFoundError(f"Thrift file not found: {thrift_file}")
                
                arango_thrift = thriftpy2.load(
                    str(thrift_file),
                    module_name="arango_thrift"
                )
                
                self._transport = TBufferedTransportFactory()
                protocol_factory = TBinaryProtocolFactory()
                self._client = make_client(
                    arango_thrift.ArangoService,
                    self.host,
                    self.port,
                    trans_factory=self._transport,
                    proto_factory=protocol_factory
                )
            except Exception as e:
                raise ConnectionError(f"Failed to connect to Thrift server at {self.host}:{self.port}: {e}")
    
    def save(self, collection: str, fields: Dict[str, Any]) -> Dict[str, Any]:
        """
        Сохранить документ в ArangoDB.
        
        Args:
            collection: Имя коллекции
            fields: Поля документа (все значения будут преобразованы в строки)
            
        Returns:
            Словарь с результатом: {'success': bool, 'key': str, 'error': str}
        """
        self._ensure_connection()
        
        # Преобразуем все значения в строки (как в TypeScript версии)
        string_fields: Dict[str, str] = {}
        for key, value in fields.items():
            if value is not None:
                string_fields[key] = str(value)
        
        try:
            # Используем динамическую версию с thriftpy2
            response = self._client.save(collection=collection, fields=string_fields)
            return {
                'success': response.success if hasattr(response, 'success') else response.get('success', False),
                'key': response.key if hasattr(response, 'key') and response.key else response.get('key'),
                'error': response.error if hasattr(response, 'error') and response.error else response.get('error')
            }
        except Exception as e:
            return {
                'success': False,
                'key': None,
                'error': str(e)
            }
    
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
            # Используем динамическую версию с thriftpy2
            response = self._client.get(collection=collection, key=key)
            
            # Обрабатываем ответ (может быть объект или словарь)
            if hasattr(response, 'fields'):
                fields = response.fields
                error = response.error if hasattr(response, 'error') else None
            else:
                fields = response.get('fields')
                error = response.get('error')
            
            return {
                'fields': dict(fields) if fields else None,
                'error': error if error else None
            }
        except Exception as e:
            return {
                'fields': None,
                'error': str(e)
            }
    
    def close(self):
        """Закрыть соединение."""
        if self._client:
            try:
                if hasattr(self._client, 'close'):
                    self._client.close()
            except:
                pass
        self._client = None
        self._transport = None
    
    def __enter__(self):
        """Контекстный менеджер."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Закрытие при выходе из контекста."""
        self.close()

