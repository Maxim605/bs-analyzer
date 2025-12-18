"""
DTO для анализа матрицы Лапласа.
"""
from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List, Optional


class LaplacianAnalysisParamsDTO(BaseModel):
    """Входные параметры для анализа матрицы Лапласа (задаваемые вручную)."""
    zero_tol: float = Field(default=1e-8, description="Допустимая погрешность для определения нуля")
    T_low_abs: float = Field(default=2.0, description="Абсолютный порог низкой частоты")
    alpha: float = Field(default=0.02, description="Коэффициент для T_low_rel = alpha * lambda_max")
    gap_factor: float = Field(default=3.0, description="Множитель для определения значимого eigengap")
    gap_ratio: float = Field(default=1.5, description="Соотношение для значимости eigengap")
    frac_many_thresh: float = Field(default=0.2, description="Порог доли малых λ для 'много'")
    k_search_fraction: float = Field(default=0.5, description="Доля спектра для поиска eigengaps")
    max_k_search: int = Field(default=50, description="Максимальное количество eigengaps для поиска")


class DegreeStatsDTO(BaseModel):
    """Статистики степеней вершин."""
    d_max: float = Field(description="Максимальная степень")
    d_avg: float = Field(description="Средняя степень")
    d_min: float = Field(description="Минимальная степень")


class IPRResultDTO(BaseModel):
    """Результат вычисления IPR для собственного вектора."""
    index: int = Field(description="Индекс собственного вектора")
    eigenvalue: float = Field(description="Соответствующее собственное число")
    ipr: float = Field(description="Inverse Participation Ratio")
    is_localized: bool = Field(description="Является ли вектор локализованным")


class EigengapDTO(BaseModel):
    """Информация о eigengap."""
    index: int = Field(description="Индекс (номер gap)")
    gap_value: float = Field(description="Значение gap")
    is_significant: bool = Field(description="Является ли gap значимым")
    gap_ratio_to_median: float = Field(description="Отношение gap к медиане")


class KCandidateDTO(BaseModel):
    """Кандидат для количества кластеров."""
    k: int = Field(description="Предлагаемое количество кластеров")
    gap_index: int = Field(description="Индекс eigengap")
    gap_value: float = Field(description="Значение eigengap")
    confidence: str = Field(description="Уровень уверенности: high/medium/low")
    reason: str = Field(description="Причина выбора")


class ConnectivityAssessmentDTO(BaseModel):
    """Оценка связности графа."""
    n_components: int = Field(description="Количество компонент связности (n_zero)")
    is_connected: bool = Field(description="Граф связен (n_components == 1)")
    lambda_2: float = Field(description="Алгебраическая связность (Fiedler)")
    lambda_2_interpretation: str = Field(description="Интерпретация lambda_2")
    recommendation: str = Field(description="Рекомендация по связности")


class LowFrequencyAssessmentDTO(BaseModel):
    """Оценка низкочастотной части спектра."""
    T_low_rel: float = Field(description="Относительный порог (alpha * lambda_max)")
    T_low_used: float = Field(description="Использованный порог")
    n_low: int = Field(description="Количество собственных чисел ≤ T_low")
    fraction_low: float = Field(description="Доля малых собственных чисел")
    assessment: str = Field(description="Оценка: few/moderate/many/very_many")
    interpretation: str = Field(description="Интерпретация результата")


class LocalizationAssessmentDTO(BaseModel):
    """Оценка локализации собственных векторов."""
    ipr_summary: List[IPRResultDTO] = Field(description="IPR для первых k векторов")
    localized_count: int = Field(description="Количество локализованных векторов")
    has_anomalies: bool = Field(description="Есть ли аномалии в первых векторах")
    recommendation: str = Field(description="Рекомендация по локализации")


class ComputedConstantsDTO(BaseModel):
    """Вычисляемые константы из матрицы Лапласа."""
    N: int = Field(description="Число вершин (размер матрицы)")
    lambda_max: float = Field(description="Максимальное собственное число")
    lambda_min: float = Field(description="Минимальное собственное число")
    lambda_2: float = Field(description="Второе собственное число (Fiedler)")
    n_zero: int = Field(description="Количество нулевых собственных чисел")
    eigenvalues: List[float] = Field(description="Все собственные числа (по возрастанию)")
    eigengaps: List[EigengapDTO] = Field(description="Разности между соседними собственными числами")
    degree_stats: DegreeStatsDTO = Field(description="Статистики степеней вершин")


class LaplacianAnalysisResponseDTO(BaseModel):
    """Полный результат анализа матрицы Лапласа."""
    # Входные параметры
    params: LaplacianAnalysisParamsDTO = Field(description="Использованные параметры")
    
    # Вычисленные константы
    computed_constants: ComputedConstantsDTO = Field(description="Вычисленные константы")
    
    # Оценки
    connectivity_assessment: ConnectivityAssessmentDTO = Field(description="Оценка связности")
    low_frequency_assessment: LowFrequencyAssessmentDTO = Field(description="Оценка низких частот")
    localization_assessment: LocalizationAssessmentDTO = Field(description="Оценка локализации")
    
    # Рекомендации по k
    k_candidates: List[KCandidateDTO] = Field(description="Кандидаты для количества кластеров")
    
    # Общие рекомендации
    summary: str = Field(description="Краткое резюме анализа")
    recommendations: List[str] = Field(description="Список рекомендаций")

