"""
Примеры использования gRPC-клиента для ArangoDB.

Демонстрирует все три режима работы:
1. Синхронный режим
2. Асинхронный режим
3. Потоковый режим
"""

import asyncio
from typing import AsyncIterator
from src.infrastructure.arango.grpc_client import ArangoGrpcClient


def example_sync_mode():
    """Пример синхронного режима работы."""
    print("=== Синхронный режим ===")
    
    # Использование контекстного менеджера
    with ArangoGrpcClient(host="localhost", port=50051) as client:
        # Сохранение документа
        result = client.save_sync(
            collection="users",
            fields={"name": "John", "age": "30", "email": "john@example.com"}
        )
        print(f"Сохранение: {result}")
        
        if result['success']:
            # Получение документа
            doc = client.get_sync(collection="users", key=result['key'])
            print(f"Получение: {doc}")
        
        # Пакетное сохранение
        requests = [
            {"collection": "users", "fields": {"name": "Alice", "age": "25"}},
            {"collection": "users", "fields": {"name": "Bob", "age": "35"}},
            {"collection": "users", "fields": {"name": "Charlie", "age": "28"}},
        ]
        results = client.save_batch_sync(requests)
        print(f"Пакетное сохранение: {len(results)} документов")


async def example_async_mode():
    """Пример асинхронного режима работы."""
    print("\n=== Асинхронный режим ===")
    
    # Использование асинхронного контекстного менеджера
    async with ArangoGrpcClient(host="localhost", port=50051) as client:
        # Сохранение документа
        result = await client.save_async(
            collection="posts",
            fields={"title": "Hello", "content": "World", "author": "John"}
        )
        print(f"Сохранение: {result}")
        
        if result['success']:
            # Получение документа
            doc = await client.get_async(collection="posts", key=result['key'])
            print(f"Получение: {doc}")
        
        # Пакетное сохранение с использованием TaskGroup (Python 3.14)
        requests = [
            {"collection": "posts", "fields": {"title": "Post 1", "content": "Content 1"}},
            {"collection": "posts", "fields": {"title": "Post 2", "content": "Content 2"}},
            {"collection": "posts", "fields": {"title": "Post 3", "content": "Content 3"}},
        ]
        results = await client.save_batch_async(requests)
        print(f"Пакетное сохранение: {len(results)} документов")
        
        # Пакетное получение
        get_requests = [
            {"collection": "posts", "key": results[0].get('key', '')},
            {"collection": "posts", "key": results[1].get('key', '')},
        ]
        docs = await client.get_batch_async(get_requests)
        print(f"Пакетное получение: {len(docs)} документов")


async def example_streaming_mode():
    """Пример потокового режима работы."""
    print("\n=== Потоковый режим ===")
    
    async with ArangoGrpcClient(host="localhost", port=50051) as client:
        # Server streaming - получение нескольких документов потоком
        print("Server streaming:")
        keys = ["key1", "key2", "key3"]
        async for doc in client.stream_get_async(collection="users", keys=keys):
            print(f"  Получен документ: {doc}")
        
        # Client streaming - отправка нескольких документов потоком
        print("\nClient streaming:")
        async def generate_requests() -> AsyncIterator[dict]:
            for i in range(3):
                yield {
                    "collection": "logs",
                    "fields": {"message": f"Log entry {i}", "level": "info"}
                }
        
        result = await client.stream_save_async(generate_requests())
        print(f"  Результат: {result}")
        
        # Bidirectional streaming - двунаправленный поток
        print("\nBidirectional streaming:")
        async def generate_batch_requests() -> AsyncIterator[dict]:
            for i in range(5):
                yield {
                    "collection": "events",
                    "fields": {"event_id": str(i), "type": "user_action"}
                }
        
        async for response in client.stream_batch_async(generate_batch_requests()):
            print(f"  Ответ: {response}")


def example_sync_streaming():
    """Пример синхронного потокового режима."""
    print("\n=== Синхронный потоковый режим ===")
    
    with ArangoGrpcClient(host="localhost", port=50051) as client:
        keys = ["key1", "key2", "key3"]
        for doc in client.stream_get_sync(collection="users", keys=keys):
            print(f"  Получен документ: {doc}")


async def main():
    """Главная функция с примерами всех режимов."""
    try:
        # Синхронный режим
        example_sync_mode()
        
        # Асинхронный режим
        await example_async_mode()
        
        # Потоковый режим
        await example_streaming_mode()
        
        # Синхронный потоковый режим
        example_sync_streaming()
        
    except Exception as e:
        print(f"Ошибка: {e}")
        print("Убедитесь, что gRPC-сервер запущен на localhost:50051")


if __name__ == "__main__":
    asyncio.run(main())




