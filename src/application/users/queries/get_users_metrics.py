"""
Обработчик для вычисления метрик по данным пользователей.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import statistics

from src.infrastructure.users.db.users_db import UsersDb


@dataclass
class GetUsersMetricsHandler:
    """
    Обработчик для расчета метрик по данным пользователей.

    - Получает данные через UsersDb
    - Вычисляет статистику по числовым и категориальным полям
    """

    db: UsersDb

    async def execute(
        self,
        user_ids: List[str],
        numeric_fields: List[str],
        categorical_fields: List[str],
        fillna_mean: bool = False,
        fillna: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Получить метрики по пользователям.

        Args:
            user_ids: Список ID пользователей
            numeric_fields: Числовые поля для анализа
            categorical_fields: Категориальные поля для анализа
            fillna_mean: Заполнять пустые значения средним (для числовых)
            fillna: Значение для заполнения пустот (для категориальных)

        Returns:
            Словарь с метриками
        """
        # Получаем данные пользователей
        users_data = await self.db.get_users_by_ids(user_ids)

        # Подсчет статистики
        total_users = len(user_ids)
        users_found = sum(1 for u in users_data if u.get("fields") is not None)
        users_with_errors = sum(1 for u in users_data if u.get("error") is not None)

        # Извлекаем только успешно полученные данные
        valid_users = [u for u in users_data if u.get("fields") is not None]

        # Рассчитываем метрики по числовым полям
        numeric_stats = []
        for field in numeric_fields:
            stats = self._calculate_numeric_stats(
                valid_users, field, fillna_mean
            )
            numeric_stats.append(stats)

        # Рассчитываем метрики по категориальным полям
        categorical_stats = []
        for field in categorical_fields:
            stats = self._calculate_categorical_stats(
                valid_users, field, fillna
            )
            categorical_stats.append(stats)

        return {
            "total_users": total_users,
            "users_found": users_found,
            "users_with_errors": users_with_errors,
            "numeric_stats": numeric_stats,
            "categorical_stats": categorical_stats,
        }

    def _calculate_numeric_stats(
        self,
        users: List[Dict[str, Any]],
        field: str,
        fillna_mean: bool,
    ) -> Dict[str, Any]:
        """Рассчитать статистику по числовому полю."""
        values: List[float] = []
        count_missing = 0

        for user in users:
            fields = user.get("fields", {})
            if fields is None:
                fields = {}

            raw_value = fields.get(field)

            if raw_value is None or raw_value == "" or raw_value == "None":
                count_missing += 1
                continue

            try:
                # Пробуем преобразовать в float
                val = float(raw_value)
                values.append(val)
            except (ValueError, TypeError):
                count_missing += 1

        # Если fillna_mean и есть пустые значения - заполняем средним
        if fillna_mean and count_missing > 0 and len(values) > 0:
            mean_val = statistics.mean(values)
            # Добавляем среднее значение вместо пропущенных
            values.extend([mean_val] * count_missing)
            count_missing = 0

        # Рассчитываем статистику
        result: Dict[str, Any] = {
            "field": field,
            "count": len(values),
            "count_missing": count_missing,
            "mean": None,
            "median": None,
            "variance": None,
            "std": None,
            "min": None,
            "max": None,
            "distribution": None,
        }

        if len(values) > 0:
            result["mean"] = round(statistics.mean(values), 4)
            result["median"] = round(statistics.median(values), 4)
            result["min"] = round(min(values), 4)
            result["max"] = round(max(values), 4)

            if len(values) > 1:
                result["variance"] = round(statistics.variance(values), 4)
                result["std"] = round(statistics.stdev(values), 4)

            # Гистограмма (распределение по бакетам)
            result["distribution"] = self._build_histogram(values)

        return result

    def _calculate_categorical_stats(
        self,
        users: List[Dict[str, Any]],
        field: str,
        fillna: Optional[str],
    ) -> Dict[str, Any]:
        """Рассчитать статистику по категориальному полю."""
        distribution: Dict[str, int] = {}
        count_missing = 0

        for user in users:
            fields = user.get("fields", {})
            if fields is None:
                fields = {}

            raw_value = fields.get(field)

            if raw_value is None or raw_value == "" or raw_value == "None":
                if fillna is not None:
                    # Заполняем пропуск указанным значением
                    raw_value = fillna
                else:
                    count_missing += 1
                    continue

            # Преобразуем в строку
            str_value = str(raw_value)
            distribution[str_value] = distribution.get(str_value, 0) + 1

        # Топ значений (сортируем по частоте)
        sorted_items = sorted(
            distribution.items(), key=lambda x: x[1], reverse=True
        )
        top_values = [
            {"value": k, "count": v, "percentage": round(v / sum(distribution.values()) * 100, 2) if distribution else 0}
            for k, v in sorted_items[:10]
        ]

        return {
            "field": field,
            "count": sum(distribution.values()),
            "count_missing": count_missing,
            "unique_count": len(distribution),
            "distribution": distribution,
            "top_values": top_values,
        }

    def _build_histogram(self, values: List[float], num_bins: int = 10) -> Dict[str, int]:
        """Построить гистограмму распределения."""
        if not values:
            return {}

        min_val = min(values)
        max_val = max(values)

        # Если все значения одинаковые
        if min_val == max_val:
            return {f"{min_val:.2f}": len(values)}

        # Рассчитываем размер бакета
        bin_size = (max_val - min_val) / num_bins

        histogram: Dict[str, int] = {}
        for val in values:
            # Определяем индекс бакета
            bin_idx = min(int((val - min_val) / bin_size), num_bins - 1)
            bin_start = min_val + bin_idx * bin_size
            bin_end = bin_start + bin_size
            bin_key = f"{bin_start:.2f}-{bin_end:.2f}"
            histogram[bin_key] = histogram.get(bin_key, 0) + 1

        return histogram

