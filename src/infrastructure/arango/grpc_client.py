"""
gRPC-клиент для подключения к ArangoDB через gRPC.

Поддерживает три режима работы:
1. Синхронный - использует threading для блокирующих операций
2. Асинхронный - использует asyncio для неблокирующих операций
3. Потоковый - поддерживает server streaming, client streaming и bidirectional streaming

Использует возможности многопоточности Python 3.14:
- asyncio.TaskGroup для параллельных операций
- threading для синхронных операций
- concurrent.futures для пула потоков
"""

from __future__ import annotations

import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import AsyncIterator, Iterator, Optional, Dict, Any, List
import grpc
from grpc import aio

# Импорты сгенерированных proto-файлов (будут созданы после генерации)
# Путь будет зависеть от структуры проекта
import sys
from pathlib import Path

# Добавляем корень проекта в путь для импорта proto
project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    import proto.arango_pb2 as arango_pb2
    import proto.arango_pb2_grpc as arango_pb2_grpc
except ImportError:
    # Временная заглушка для разработки
    arango_pb2 = None
    arango_pb2_grpc = None


class ArangoGrpcClient:
    """
    gRPC-клиент для работы с ArangoDB.
    
    Поддерживает синхронный, асинхронный и потоковый режимы работы.
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 50051,
        max_workers: int = 10,
        use_ssl: bool = False,
    ):
        """
        Инициализация gRPC-клиента.
        
        Args:
            host: Хост gRPC-сервера
            port: Порт gRPC-сервера
            max_workers: Максимальное количество потоков для синхронных операций
            use_ssl: Использовать SSL/TLS для подключения
        """
        self.host = host
        self.port = port
        self.max_workers = max_workers
        self.use_ssl = use_ssl
        self._channel: Optional[grpc.Channel] = None
        self._async_channel: Optional[aio.Channel] = None
        self._stub: Optional[Any] = None
        self._async_stub: Optional[Any] = None
        self._executor: Optional[ThreadPoolExecutor] = None
        self._lock = threading.Lock()
        
    def _get_channel(self) -> grpc.Channel:
        """Получить или создать синхронный канал."""
        if self._channel is None:
            with self._lock:
                if self._channel is None:
                    target = f"{self.host}:{self.port}"
                    if self.use_ssl:
                        credentials = grpc.ssl_channel_credentials()
                        self._channel = grpc.secure_channel(target, credentials)
                    else:
                        self._channel = grpc.insecure_channel(target)
        return self._channel
    
    def _get_stub(self) -> Any:
        """Получить или создать синхронный stub."""
        if self._stub is None:
            if arango_pb2_grpc is None:
                raise ImportError("gRPC stubs not generated. Run: python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. proto/arango.proto")
            channel = self._get_channel()
            self._stub = arango_pb2_grpc.ArangoServiceStub(channel)
        return self._stub
    
    async def _get_async_channel(self) -> aio.Channel:
        """Получить или создать асинхронный канал."""
        if self._async_channel is None:
            target = f"{self.host}:{self.port}"
            if self.use_ssl:
                credentials = grpc.ssl_channel_credentials()
                self._async_channel = aio.secure_channel(target, credentials)
            else:
                self._async_channel = aio.insecure_channel(target)
        return self._async_channel
    
    async def _get_async_stub(self) -> Any:
        """Получить или создать асинхронный stub."""
        if self._async_stub is None:
            if arango_pb2_grpc is None:
                raise ImportError("gRPC stubs not generated. Run: python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. proto/arango.proto")
            channel = await self._get_async_channel()
            self._async_stub = arango_pb2_grpc.ArangoServiceStub(channel)
        return self._async_stub
    
    def _get_executor(self) -> ThreadPoolExecutor:
        """Получить или создать пул потоков."""
        if self._executor is None:
            with self._lock:
                if self._executor is None:
                    self._executor = ThreadPoolExecutor(max_workers=self.max_workers)
        return self._executor
    
    # ==================== СИНХРОННЫЙ РЕЖИМ ====================
    
    def save_sync(self, collection: str, fields: Dict[str, str]) -> Dict[str, Any]:
        """
        Синхронное сохранение документа.
        
        Args:
            collection: Имя коллекции
            fields: Поля документа (словарь строк)
            
        Returns:
            Словарь с результатом: {'success': bool, 'key': str, 'error': str}
        """
        if arango_pb2 is None:
            raise ImportError("gRPC protobuf not generated")
        
        stub = self._get_stub()
        request = arango_pb2.SaveRequest(
            collection=collection,
            fields=fields
        )
        response = stub.Save(request)
        
        return {
            'success': response.success,
            'key': response.key,
            'error': response.error if response.error else None
        }
    
    def get_sync(self, collection: str, key: str) -> Dict[str, Any]:
        """
        Синхронное получение документа.
        
        Args:
            collection: Имя коллекции
            key: Ключ документа
            
        Returns:
            Словарь с результатом: {'fields': dict, 'error': str}
        """
        if arango_pb2 is None:
            raise ImportError("gRPC protobuf not generated")
        
        stub = self._get_stub()
        request = arango_pb2.GetRequest(
            collection=collection,
            key=key
        )
        response = stub.Get(request)
        
        return {
            'fields': dict(response.fields) if response.fields else None,
            'error': response.error if response.error else None
        }
    
    def save_batch_sync(self, requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Синхронное пакетное сохранение документов с использованием пула потоков.
        
        Args:
            requests: Список запросов, каждый содержит 'collection' и 'fields'
            
        Returns:
            Список результатов сохранения
        """
        executor = self._get_executor()
        futures = []
        
        for req in requests:
            future = executor.submit(
                self.save_sync,
                req['collection'],
                req['fields']
            )
            futures.append(future)
        
        results = []
        for future in as_completed(futures):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                results.append({'success': False, 'error': str(e)})
        
        return results
    
    # ==================== АСИНХРОННЫЙ РЕЖИМ ====================
    
    async def save_async(self, collection: str, fields: Dict[str, str]) -> Dict[str, Any]:
        """
        Асинхронное сохранение документа.
        
        Args:
            collection: Имя коллекции
            fields: Поля документа (словарь строк)
            
        Returns:
            Словарь с результатом: {'success': bool, 'key': str, 'error': str}
        """
        if arango_pb2 is None:
            raise ImportError("gRPC protobuf not generated")
        
        stub = await self._get_async_stub()
        request = arango_pb2.SaveRequest(
            collection=collection,
            fields=fields
        )
        response = await stub.Save(request)
        
        return {
            'success': response.success,
            'key': response.key,
            'error': response.error if response.error else None
        }
    
    async def get_async(self, collection: str, key: str) -> Dict[str, Any]:
        """
        Асинхронное получение документа.
        
        Args:
            collection: Имя коллекции
            key: Ключ документа
            
        Returns:
            Словарь с результатом: {'fields': dict, 'error': str}
        """
        if arango_pb2 is None:
            raise ImportError("gRPC protobuf not generated")
        
        stub = await self._get_async_stub()
        request = arango_pb2.GetRequest(
            collection=collection,
            key=key
        )
        response = await stub.Get(request)
        
        return {
            'fields': dict(response.fields) if response.fields else None,
            'error': response.error if response.error else None
        }
    
    async def save_batch_async(self, requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Асинхронное пакетное сохранение документов с использованием TaskGroup (Python 3.14).
        
        Args:
            requests: Список запросов, каждый содержит 'collection'和'fields'
            
        Returns:
            Список результатов сохранения
        """
        async def save_one(req: Dict[str, Any]) -> Dict[str, Any]:
            try:
                return await self.save_async(req['collection'], req['fields'])
            except Exception as e:
                return {'success': False, 'error': str(e)}
        
        # Используем TaskGroup для параллельного выполнения (Python 3.11+)
        try:
            async with asyncio.TaskGroup() as tg:
                tasks = [tg.create_task(save_one(req)) for req in requests]
            
            # TaskGroup автоматически собирает результаты
            return [task.result() for task in tasks]
        except (AttributeError, RuntimeError):
            # Fallback для версий Python < 3.11 (TaskGroup доступен с 3.11)
            tasks = [save_one(req) for req in requests]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            # Преобразуем исключения в словари с ошибками
            return [
                result if isinstance(result, dict) else {'success': False, 'error': str(result)}
                for result in results
            ]
    
    async def get_batch_async(self, requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Асинхронное пакетное получение документов с использованием TaskGroup (Python 3.14).
        
        Args:
            requests: Список запросов, каждый содержит 'collection' и 'key'
            
        Returns:
            Список результатов получения
        """
        async def get_one(req: Dict[str, Any]) -> Dict[str, Any]:
            try:
                return await self.get_async(req['collection'], req['key'])
            except Exception as e:
                return {'error': str(e)}
        
        # Используем TaskGroup для параллельного выполнения (Python 3.11+)
        try:
            async with asyncio.TaskGroup() as tg:
                tasks = [tg.create_task(get_one(req)) for req in requests]
            
            # TaskGroup автоматически собирает результаты
            return [task.result() for task in tasks]
        except (AttributeError, RuntimeError):
            # Fallback для версий Python < 3.11
            tasks = [get_one(req) for req in requests]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            # Преобразуем исключения в словари с ошибками
            return [
                result if isinstance(result, dict) else {'error': str(result)}
                for result in results
            ]
    
    # ==================== ПОТОКОВЫЙ РЕЖИМ ====================
    
    def stream_get_sync(
        self,
        collection: str,
        keys: List[str]
    ) -> Iterator[Dict[str, Any]]:
        """
        Синхронное потоковое получение документов (server streaming).
        
        Args:
            collection: Имя коллекции
            keys: Список ключей документов
            
        Yields:
            Словари с результатами получения документов
        """
        if arango_pb2 is None:
            raise ImportError("gRPC protobuf not generated")
        
        stub = self._get_stub()
        request = arango_pb2.StreamGetRequest(
            collection=collection,
            keys=keys
        )
        
        try:
            for response in stub.StreamGet(request):
                yield {
                    'fields': dict(response.fields) if response.fields else None,
                    'error': response.error if response.error else None
                }
        except grpc.RpcError as e:
            yield {'error': f"gRPC error: {e.code()}: {e.details()}"}
    
    async def stream_get_async(
        self,
        collection: str,
        keys: List[str]
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Асинхронное потоковое получение документов (server streaming).
        
        Args:
            collection: Имя коллекции
            keys: Список ключей документов
            
        Yields:
            Словари с результатами получения документов
        """
        if arango_pb2 is None:
            raise ImportError("gRPC protobuf not generated")
        
        stub = await self._get_async_stub()
        request = arango_pb2.StreamGetRequest(
            collection=collection,
            keys=keys
        )
        
        try:
            async for response in stub.StreamGet(request):
                yield {
                    'fields': dict(response.fields) if response.fields else None,
                    'error': response.error if response.error else None
                }
        except grpc.RpcError as e:
            yield {'error': f"gRPC error: {e.code()}: {e.details()}"}
    
    async def stream_save_async(
        self,
        requests: AsyncIterator[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Асинхронное потоковое сохранение документов (client streaming).
        
        Args:
            requests: Асинхронный итератор запросов, каждый содержит 'collection' и 'fields'
            
        Returns:
            Итоговый результат сохранения
        """
        if arango_pb2 is None:
            raise ImportError("gRPC protobuf not generated")
        
        stub = await self._get_async_stub()
        
        async def request_iterator():
            async for req in requests:
                yield arango_pb2.SaveRequest(
                    collection=req['collection'],
                    fields=req['fields']
                )
        
        try:
            response = await stub.StreamSave(request_iterator())
            return {
                'success': response.success,
                'key': response.key,
                'error': response.error if response.error else None
            }
        except grpc.RpcError as e:
            return {'success': False, 'error': f"gRPC error: {e.code()}: {e.details()}"}
    
    async def stream_batch_async(
        self,
        requests: AsyncIterator[Dict[str, Any]]
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Асинхронный двунаправленный поток (bidirectional streaming).
        
        Args:
            requests: Асинхронный итератор запросов, каждый содержит 'collection' и 'fields'
            
        Yields:
            Словари с результатами сохранения документов
        """
        if arango_pb2 is None:
            raise ImportError("gRPC protobuf not generated")
        
        stub = await self._get_async_stub()
        
        async def request_iterator():
            async for req in requests:
                yield arango_pb2.SaveRequest(
                    collection=req['collection'],
                    fields=req['fields']
                )
        
        try:
            async for response in stub.StreamBatch(request_iterator()):
                yield {
                    'success': response.success,
                    'key': response.key,
                    'error': response.error if response.error else None
                }
        except grpc.RpcError as e:
            yield {'success': False, 'error': f"gRPC error: {e.code()}: {e.details()}"}
    
    # ==================== ЗАКРЫТИЕ РЕСУРСОВ ====================
    
    def close_sync(self):
        """Закрыть синхронные соединения."""
        if self._channel:
            self._channel.close()
            self._channel = None
            self._stub = None
        
        if self._executor:
            self._executor.shutdown(wait=True)
            self._executor = None
    
    async def close_async(self):
        """Закрыть асинхронные соединения."""
        if self._async_channel:
            await self._async_channel.close()
            self._async_channel = None
            self._async_stub = None
    
    async def close(self):
        """Закрыть все соединения."""
        self.close_sync()
        await self.close_async()
    
    def __enter__(self):
        """Контекстный менеджер для синхронного использования."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Закрытие при выходе из контекста."""
        self.close_sync()
    
    async def __aenter__(self):
        """Контекстный менеджер для асинхронного использования."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Закрытие при выходе из асинхронного контекста."""
        await self.close()

