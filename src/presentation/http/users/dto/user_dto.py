from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class UsersBatchRequestDTO(BaseModel):
    """Запрос на получение данных пользователей по списку ID."""

    ids: List[str] = Field(..., description="Список идентификаторов пользователей")


class UserDTO(BaseModel):
    """Данные одного пользователя из ArangoDB."""

    id: str = Field(..., description="Идентификатор пользователя")
    data: Optional[Dict[str, str]] = Field(
        None, description="Поля документа пользователя из ArangoDB"
    )
    error: Optional[str] = Field(
        None, description="Описание ошибки при получении пользователя, если была"
    )


# ===================== Metrics DTOs =====================


class UsersMetricsRequestDTO(BaseModel):
    """Запрос на расчет метрик по пользователям."""

    ids: List[str] = Field(..., description="Список идентификаторов пользователей")
    numeric_fields: List[str] = Field(
        default=[],
        description="Список числовых полей для анализа (среднее, медиана, дисперсия)"
    )
    categorical_fields: List[str] = Field(
        default=[],
        description="Список категориальных полей для анализа (распределение)"
    )
    fillna_mean: bool = Field(
        default=False,
        description="Заполнять пустые значения средним для числовых полей"
    )
    fillna: Optional[str] = Field(
        default=None,
        description="Значение для заполнения пустот в категориальных полях"
    )


class NumericFieldStatsDTO(BaseModel):
    """Статистика по числовому полю."""

    field: str = Field(..., description="Имя поля")
    count: int = Field(..., description="Количество значений")
    count_missing: int = Field(..., description="Количество пустых значений")
    mean: Optional[float] = Field(None, description="Среднее значение")
    median: Optional[float] = Field(None, description="Медиана")
    variance: Optional[float] = Field(None, description="Дисперсия")
    std: Optional[float] = Field(None, description="Стандартное отклонение")
    min: Optional[float] = Field(None, description="Минимум")
    max: Optional[float] = Field(None, description="Максимум")
    distribution: Optional[Dict[str, int]] = Field(
        None, description="Распределение по бакетам (гистограмма)"
    )


class CategoricalFieldStatsDTO(BaseModel):
    """Статистика по категориальному полю."""

    field: str = Field(..., description="Имя поля")
    count: int = Field(..., description="Количество значений")
    count_missing: int = Field(..., description="Количество пустых значений")
    unique_count: int = Field(..., description="Количество уникальных значений")
    distribution: Dict[str, int] = Field(
        ..., description="Распределение значений (значение -> количество)"
    )
    top_values: List[Dict[str, Any]] = Field(
        default=[], description="Топ самых частых значений"
    )


class UsersMetricsResponseDTO(BaseModel):
    """Ответ с метриками по пользователям."""

    total_users: int = Field(..., description="Всего запрошено пользователей")
    users_found: int = Field(..., description="Пользователей найдено")
    users_with_errors: int = Field(..., description="Пользователей с ошибками")
    numeric_stats: List[NumericFieldStatsDTO] = Field(
        default=[], description="Статистика по числовым полям"
    )
    categorical_stats: List[CategoricalFieldStatsDTO] = Field(
        default=[], description="Статистика по категориальным полям"
    )


