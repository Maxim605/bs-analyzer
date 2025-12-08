import json
import redis
from typing import Any

class RedisTaskManager:
    """
    Инфраструктурный сервис для работы с Redis.
    Обеспечивает кэширование и управление очередью задач (эмуляция).
    """
    def __init__(self, host: str = 'localhost', port: int = 6379, db: int = 0):
        # Используем decode_responses=True для получения str вместо bytes
        self.client = redis.Redis(host=host, port=port, db=db, decode_responses=True)

    def enqueue_clustering_task(self, graph_data: dict) -> str:
        """
        Помещает задачу кластеризации в очередь Redis.
        В реальном приложении здесь был бы Celery или другой Task Queue.
        """
        task_id = f"task:{hash(json.dumps(graph_data, sort_keys=True))}"
        # Эмуляция очереди: просто сохраняем данные, воркер бы их забрал
        self.client.rpush('clustering_queue', json.dumps({
            'task_id': task_id,
            'data': graph_data
        }))
        return task_id

    def cache_result(self, key: str, value: Any, ttl: int = 3600) -> None:
        self.client.set(key, json.dumps(value), ex=ttl)

    def get_cached_result(self, key: str) -> Any | None:
        data = self.client.get(key)
        if data:
            return json.loads(data)
        return None

    def get_task_result(self, task_id: str) -> dict | None:
        """
        Получает результат задачи по task_id.
        Ожидает, что результат сохранен с ключом result:{task_id}
        """
        result_key = f"result:{task_id}"
        data = self.client.get(result_key)
        if data:
            return json.loads(data)
        return None

    def save_task_result(self, task_id: str, result: Any, ttl: int = 3600) -> None:
        """
        Сохраняет результат задачи в Redis.
        """
        result_key = f"result:{task_id}"
        self.client.set(result_key, json.dumps(result), ex=ttl)

