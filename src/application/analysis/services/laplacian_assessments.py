"""
Функции оценок для анализа матрицы Лапласа.
"""
from __future__ import annotations
from typing import List
import numpy as np
from numpy.typing import NDArray

from src.application.analysis.dto.laplacian_analysis_dto import (
    LaplacianAnalysisParamsDTO,
    ConnectivityAssessmentDTO,
    LowFrequencyAssessmentDTO,
    LocalizationAssessmentDTO,
    KCandidateDTO,
    EigengapDTO,
    IPRResultDTO,
)


def assess_connectivity(
    n_zero: int,
    lambda_2: float,
    lambda_max: float,
    params: LaplacianAnalysisParamsDTO
) -> ConnectivityAssessmentDTO:
    """
    Оценивает связность графа на основе спектра.
    """
    is_connected = n_zero == 1
    
    # Интерпретация lambda_2
    if lambda_2 < 1e-6:
        lambda_2_interpretation = "Очень малое λ₂ указывает на почти разделённый граф"
    elif lambda_2 < params.alpha * lambda_max:
        lambda_2_interpretation = "Малое λ₂ относительно λ_max: есть слабое место в графе"
    elif lambda_2 < 0.1 * lambda_max:
        lambda_2_interpretation = "Умеренное λ₂: граф имеет выраженную структуру кластеров"
    else:
        lambda_2_interpretation = "Большое λ₂: граф хорошо связан"
    
    # Рекомендация
    if n_zero > 1:
        recommendation = f"Граф имеет {n_zero} компонент связности. Рекомендуется анализировать каждую компоненту отдельно."
    elif lambda_2 < 1e-6:
        recommendation = "Граф почти распадается. Проверьте наличие узких мест (bottlenecks)."
    else:
        recommendation = "Граф связен. Можно продолжать спектральный анализ."
    
    return ConnectivityAssessmentDTO(
        n_components=n_zero,
        is_connected=is_connected,
        lambda_2=lambda_2,
        lambda_2_interpretation=lambda_2_interpretation,
        recommendation=recommendation
    )


def assess_low_frequencies(
    eigenvalues: NDArray,
    T_low_rel: float,
    T_low_used: float,
    N: int,
    params: LaplacianAnalysisParamsDTO
) -> LowFrequencyAssessmentDTO:
    """
    Оценивает низкочастотную часть спектра.
    """
    n_low = int(np.sum(eigenvalues <= T_low_used))
    fraction_low = n_low / N if N > 0 else 0.0
    
    # Определяем оценку
    if fraction_low <= 0.1:
        assessment = "few"
        interpretation = "Мало низкочастотных мод: граф не имеет выраженной иерархической структуры"
    elif fraction_low <= params.frac_many_thresh:
        assessment = "moderate"
        interpretation = "Умеренное количество низкочастотных мод: возможна кластерная структура"
    elif fraction_low <= 0.4:
        assessment = "many"
        interpretation = "Много низкочастотных мод: выраженная иерархическая/кластерная структура"
    else:
        assessment = "very_many"
        interpretation = "Очень много низкочастотных мод: постепенная/плавная структура сообществ"
    
    return LowFrequencyAssessmentDTO(
        T_low_rel=T_low_rel,
        T_low_used=T_low_used,
        n_low=n_low,
        fraction_low=fraction_low,
        assessment=assessment,
        interpretation=interpretation
    )


def assess_localization(
    ipr_results: List[IPRResultDTO],
    k_max: int
) -> LocalizationAssessmentDTO:
    """
    Оценивает локализацию первых k собственных векторов.
    """
    # Берём только первые k_max векторов для оценки
    relevant_ipr = ipr_results[:k_max] if len(ipr_results) > k_max else ipr_results
    
    localized_count = sum(1 for ipr in relevant_ipr if ipr.is_localized)
    
    # Если первые несколько векторов (кроме первого) локализованы, это аномалия
    # Первый вектор (соответствующий λ=0) обычно равномерный
    has_anomalies = False
    if len(relevant_ipr) > 1:
        # Проверяем векторы начиная со второго
        early_localized = sum(1 for ipr in relevant_ipr[1:min(5, len(relevant_ipr))] if ipr.is_localized)
        has_anomalies = early_localized >= 2
    
    # Рекомендация
    if has_anomalies:
        recommendation = (
            "Обнаружены локализованные собственные векторы в начале спектра. "
            "Это может указывать на локальные аномалии (изолированные вершины, листья). "
            "Рекомендуется пересмотреть выбор k или исключить аномальные вершины."
        )
    elif localized_count > len(relevant_ipr) // 2:
        recommendation = (
            "Значительная часть векторов локализована. "
            "Спектральная кластеризация может дать нестабильные результаты."
        )
    else:
        recommendation = "Собственные векторы не имеют сильной локализации. Спектральный анализ применим."
    
    return LocalizationAssessmentDTO(
        ipr_summary=relevant_ipr,
        localized_count=localized_count,
        has_anomalies=has_anomalies,
        recommendation=recommendation
    )


def find_k_candidates(
    eigengaps: List[EigengapDTO],
    n_zero: int,
    params: LaplacianAnalysisParamsDTO
) -> List[KCandidateDTO]:
    """
    Находит кандидатов для количества кластеров на основе eigengaps.
    """
    candidates = []
    
    # Фильтруем значимые gaps
    significant_gaps = [(eg.index, eg.gap_value, eg.gap_ratio_to_median) 
                        for eg in eigengaps if eg.is_significant]
    
    if not significant_gaps:
        # Если нет значимых gaps, берём максимальный
        if eigengaps:
            max_gap = max(eigengaps, key=lambda x: x.gap_value)
            candidates.append(KCandidateDTO(
                k=max_gap.index + 1,
                gap_index=max_gap.index,
                gap_value=max_gap.gap_value,
                confidence="low",
                reason="Нет значимых eigengaps, выбран максимальный"
            ))
        return candidates
    
    # Сортируем по значению gap (убывание)
    significant_gaps.sort(key=lambda x: x[1], reverse=True)
    
    for i, (gap_index, gap_value, gap_ratio) in enumerate(significant_gaps[:5]):
        # k = gap_index + 1 (так как индексация с 0)
        k = gap_index + 1
        
        # Определяем уверенность
        if gap_ratio > params.gap_factor * 2:
            confidence = "high"
            reason = f"Очень значимый eigengap (ratio={gap_ratio:.2f} > {params.gap_factor * 2})"
        elif gap_ratio > params.gap_factor:
            confidence = "medium"
            reason = f"Значимый eigengap (ratio={gap_ratio:.2f} > {params.gap_factor})"
        else:
            confidence = "low"
            reason = f"Умеренный eigengap (ratio={gap_ratio:.2f})"
        
        # Учитываем количество компонент связности
        if k < n_zero:
            confidence = "low"
            reason += f" (k < n_components={n_zero}, возможно недостаточно)"
        
        candidates.append(KCandidateDTO(
            k=k,
            gap_index=gap_index,
            gap_value=gap_value,
            confidence=confidence,
            reason=reason
        ))
    
    return candidates


def generate_summary(
    N: int,
    n_zero: int,
    lambda_2: float,
    lambda_max: float,
    fraction_low: float,
    k_candidates: List[KCandidateDTO]
) -> str:
    """
    Генерирует краткое резюме анализа.
    """
    parts = [f"Анализ графа с {N} вершинами."]
    
    if n_zero > 1:
        parts.append(f"Граф состоит из {n_zero} компонент связности.")
    else:
        parts.append("Граф связен.")
    
    # Оценка связности
    relative_lambda2 = lambda_2 / lambda_max if lambda_max > 0 else 0
    if relative_lambda2 < 0.01:
        parts.append("Алгебраическая связность очень низкая.")
    elif relative_lambda2 < 0.1:
        parts.append("Алгебраическая связность умеренная.")
    else:
        parts.append("Алгебраическая связность высокая.")
    
    # Оценка кластеров
    if k_candidates:
        best_k = k_candidates[0]
        parts.append(f"Рекомендуемое k={best_k.k} (уверенность: {best_k.confidence}).")
    
    return " ".join(parts)


def generate_recommendations(
    connectivity: ConnectivityAssessmentDTO,
    low_freq: LowFrequencyAssessmentDTO,
    localization: LocalizationAssessmentDTO,
    k_candidates: List[KCandidateDTO]
) -> List[str]:
    """
    Генерирует список рекомендаций на основе всех оценок.
    """
    recommendations = []
    
    # Рекомендации по связности
    if not connectivity.is_connected:
        recommendations.append(
            f"Граф несвязен ({connectivity.n_components} компонент). "
            "Рекомендуется анализировать каждую компоненту отдельно."
        )
    
    if connectivity.lambda_2 < 1e-6 and connectivity.is_connected:
        recommendations.append(
            "Очень низкая алгебраическая связность указывает на наличие узкого места. "
            "Проверьте граф на наличие мостов."
        )
    
    # Рекомендации по низким частотам
    if low_freq.assessment in ["many", "very_many"]:
        recommendations.append(
            f"Высокая доля низкочастотных мод ({low_freq.fraction_low:.1%}) указывает на "
            "иерархическую структуру. Рассмотрите иерархическую кластеризацию."
        )
    
    # Рекомендации по локализации
    if localization.has_anomalies:
        recommendations.append(
            "Обнаружены локализованные собственные векторы. "
            "Рекомендуется проверить граф на наличие изолированных вершин или листьев."
        )
    
    # Рекомендации по k
    if k_candidates:
        high_conf = [k for k in k_candidates if k.confidence == "high"]
        if high_conf:
            recommendations.append(
                f"Наиболее надёжный выбор: k={high_conf[0].k} (высокая уверенность на основе eigengap)."
            )
        else:
            recommendations.append(
                "Нет кандидатов с высокой уверенностью. "
                "Рекомендуется провести валидацию с несколькими значениями k."
            )
    else:
        recommendations.append(
            "Не удалось определить кандидатов для k. "
            "Рассмотрите использование других методов выбора количества кластеров."
        )
    
    # Общая рекомендация по валидации
    recommendations.append(
        "Для окончательного выбора k рекомендуется провести кластеризацию с несколькими "
        "значениями и оценить качество с помощью silhouette score, modularity и стабильности."
    )
    
    return recommendations

