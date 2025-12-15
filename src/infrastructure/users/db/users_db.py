from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Dict, List

from src.infrastructure.config import config
from src.infrastructure.thrift import ThriftArangoClient
from src.infrastructure.users.db.arango_direct import ArangoDirectClient


@dataclass
class UsersDb:
    """
    DB-модуль для работы с пользователями в ArangoDB.

    Отвечает только за взаимодействие с БД и преобразование низкоуровневых ошибок
    в удобный для application-слоя формат.
    
    Использует Thrift клиент (как в референсной TypeScript реализации).
    """

    host: str = field(default_factory=lambda: config.THRIFT_HOST)
    port: int = field(default_factory=lambda: config.THRIFT_PORT)
    collection: str = field(default_factory=lambda: config.USERS_COLLECTION)
    batch_size: int = field(default_factory=lambda: config.BATCH_SIZE)

    async def get_users_by_ids(self, user_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Получить документы пользователей по списку ID.

        Возвращает список словарей:
        {
            "id": <user_id>,
            "fields": <dict | None>,
            "error": <str | None>
        }
        """
        if not user_ids:
            return []

        results: List[Dict[str, Any]] = []

        # Пробуем сначала Thrift клиент, если не работает - используем прямое подключение
        client = None
        
        # Пробуем Thrift
        try:
            test_client = ThriftArangoClient(host=self.host, port=self.port)
            # Пробуем сделать тестовый запрос для проверки подключения
            with test_client:
                test_client._ensure_connection()
                # Если дошли сюда, Thrift работает
                client = ThriftArangoClient(host=self.host, port=self.port)
        except Exception as e:
            # Thrift не доступен, пробуем прямое подключение
            try:
                test_direct = ArangoDirectClient()
                with test_direct:
                    test_direct._ensure_connection()
                    # Если дошли сюда, прямое подключение работает
                    client = ArangoDirectClient()
            except Exception as direct_e:
                # Оба способа не работают
                msg = f"Neither Thrift server (port {self.port}) nor direct ArangoDB connection available. Thrift: {str(e)}, Direct: {str(direct_e)}"
                return [
                    {
                        "id": user_id,
                        "fields": None,
                        "error": msg,
                    }
                    for user_id in user_ids
                ]
        
        # Используем выбранный клиент
        try:
            with client:
                # Обрабатываем батчами
                for start in range(0, len(user_ids), self.batch_size):
                    chunk = user_ids[start : start + self.batch_size]
                    
                    # Запускаем запросы параллельно в executor
                    loop = asyncio.get_event_loop()
                    tasks = [
                        loop.run_in_executor(
                            None,
                            client.get,
                            self.collection,
                            user_id
                        )
                        for user_id in chunk
                    ]
                    
                    batch_docs = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # Обрабатываем результаты
                    for user_id, doc in zip(chunk, batch_docs):
                        if isinstance(doc, Exception):
                            results.append(
                                {
                                    "id": user_id,
                                    "fields": None,
                                    "error": str(doc),
                                }
                            )
                        else:
                            results.append(
                                {
                                    "id": user_id,
                                    "fields": doc.get("fields"),
                                    "error": doc.get("error"),
                                }
                            )

            return results

        except Exception as e:
            # Общий fallback
            msg = str(e)
            return [
                {
                    "id": user_id,
                    "fields": None,
                    "error": msg,
                }
                for user_id in user_ids
            ]


