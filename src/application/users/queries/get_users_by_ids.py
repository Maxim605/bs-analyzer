from __future__ import annotations

from typing import Any, Dict, List

from dataclasses import dataclass

from src.infrastructure.users.db.users_db import UsersDb


@dataclass
class GetUsersByIdsHandler:
    """
    Обработчик для получения данных пользователей по списку ID.

    Делегирует работу DB-модулю, который ходит в ArangoDB батчами.
    """

    db: UsersDb

    async def execute(self, user_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Получить данные пользователей по списку идентификаторов.

        Возвращает список словарей вида:
        {
            "id": <user_id>,
            "fields": <dict | None>,
            "error": <str | None>
        }
        """
        return await self.db.get_users_by_ids(user_ids)


