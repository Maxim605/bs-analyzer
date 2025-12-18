"""
Функции вычисления констант из матрицы Лапласа.
"""
from __future__ import annotations
from typing import Tuple, List
import numpy as np
from numpy.typing import NDArray

from src.application.analysis.dto.laplacian_analysis_dto import (
    LaplacianAnalysisParamsDTO,
    DegreeStatsDTO,
    EigengapDTO,
    IPRResultDTO,
)


def validate_matrix_square(matrix: NDArray) -> None:
    """Проверяет, что матрица квадратная."""
    if matrix.ndim != 2:
        raise ValueError(f"Матрица должна быть 2D, получено: {matrix.ndim}D")
    if matrix.shape[0] != matrix.shape[1]:
        raise ValueError(f"Матрица должна быть квадратной, получено: {matrix.shape}")


def validate_matrix_symmetric(matrix: NDArray, rtol: float = 1e-5) -> None:
    """Проверяет, что матрица симметрична."""
    if not np.allclose(matrix, matrix.T, rtol=rtol):
        raise ValueError("Матрица не является симметричной")


def validate_matrix_numeric(matrix: NDArray) -> None:
    """Проверяет, что все элементы матрицы числовые."""
    if not np.issubdtype(matrix.dtype, np.number):
        raise ValueError(f"Матрица должна содержать числовые значения, получено: {matrix.dtype}")
    if np.any(np.isnan(matrix)) or np.any(np.isinf(matrix)):
        raise ValueError("Матрица содержит NaN или Inf значения")


def symmetrize_matrix(matrix: NDArray) -> NDArray:
    """Симметризует матрицу: (M + M.T) / 2."""
    return (matrix + matrix.T) / 2


def compute_spectrum(matrix: NDArray) -> Tuple[NDArray, NDArray]:
    """
    Вычисляет собственные числа и собственные векторы симметричной матрицы.
    Возвращает отсортированные по возрастанию.
    """
    eigenvalues, eigenvectors = np.linalg.eigh(matrix)
    # eigh уже возвращает отсортированные по возрастанию
    return eigenvalues, eigenvectors


def compute_n_vertices(matrix: NDArray) -> int:
    """Вычисляет N — число вершин (размер матрицы)."""
    return matrix.shape[0]


def compute_lambda_max(eigenvalues: NDArray) -> float:
    """Вычисляет λ_max = max_i λ_i."""
    return float(eigenvalues[-1])


def compute_lambda_min(eigenvalues: NDArray) -> float:
    """Вычисляет λ_min = min_i λ_i (обычно ≈ 0)."""
    return float(eigenvalues[0])


def compute_lambda_2(eigenvalues: NDArray) -> float:
    """Вычисляет λ₂ (второе по порядку, Fiedler)."""
    if len(eigenvalues) < 2:
        return 0.0
    return float(eigenvalues[1])


def compute_n_zero(eigenvalues: NDArray, zero_tol: float) -> int:
    """Вычисляет n_zero — число собственных чисел, численно равных нулю."""
    return int(np.sum(np.abs(eigenvalues) <= zero_tol))


def compute_eigengaps_raw(eigenvalues: NDArray) -> NDArray:
    """Вычисляет массив разностей g_i = λ_{i+1} - λ_i."""
    return np.diff(eigenvalues)


def compute_eigengaps(
    eigenvalues: NDArray,
    params: LaplacianAnalysisParamsDTO,
    lambda_max: float
) -> List[EigengapDTO]:
    """
    Вычисляет eigengaps с оценкой значимости.
    
    Eigengaps - это разности между соседними собственными числами: g_i = λ_{i+1} - λ_i.
    Большие gaps указывают на возможные границы между кластерами.
    """
    gaps = compute_eigengaps_raw(eigenvalues)
    
    # Ограничиваем количество gaps для анализа
    n_search = min(
        int(len(gaps) * params.k_search_fraction),
        params.max_k_search,
        len(gaps)
    )
    
    # Вычисляем медиану только для релевантных gaps (исключаем нулевые/очень маленькие)
    # Это предотвращает огромные значения gap_ratio_to_median
    relevant_gaps = gaps[:n_search]
    # Исключаем gaps, которые численно равны нулю (с учётом погрешности)
    non_zero_gaps = relevant_gaps[relevant_gaps > params.zero_tol]
    
    if len(non_zero_gaps) > 0:
        median_gap = float(np.median(non_zero_gaps))
    else:
        # Если все gaps нулевые, используем медиану всех gaps
        median_gap = float(np.median(gaps)) if len(gaps) > 0 else 0.0
    
    # Если медиана всё ещё очень маленькая (близка к нулю), используем среднее значение
    # для более устойчивой оценки
    if median_gap < params.zero_tol:
        mean_gap = float(np.mean(relevant_gaps[relevant_gaps > params.zero_tol])) if len(non_zero_gaps) > 0 else 0.0
        if mean_gap > params.zero_tol:
            median_gap = mean_gap
    
    result = []
    for i in range(n_search):
        gap_value = float(gaps[i])
        
        # Проверяем значимость по нескольким критериям
        is_significant_by_factor = False
        if median_gap > params.zero_tol:
            is_significant_by_factor = gap_value > params.gap_factor * median_gap
        
        is_significant_by_absolute = gap_value > params.alpha * lambda_max if lambda_max > 0 else False
        
        is_significant = is_significant_by_factor or is_significant_by_absolute
        
        # Вычисляем gap_ratio с защитой от деления на очень маленькие числа
        if median_gap > params.zero_tol:
            gap_ratio = gap_value / median_gap
            # Ограничиваем разумным максимумом для читаемости (например, 1000)
            # Но сохраняем оригинальное значение для логики
            gap_ratio_display = min(gap_ratio, 1000.0) if gap_ratio < float('inf') else 1000.0
        else:
            gap_ratio = 0.0
            gap_ratio_display = 0.0
        
        result.append(EigengapDTO(
            index=i,
            gap_value=gap_value,
            is_significant=is_significant,
            gap_ratio_to_median=gap_ratio_display  # Используем ограниченное значение для отображения
        ))
    
    return result


def compute_fraction_low(eigenvalues: NDArray, T_low: float, N: int) -> float:
    """Вычисляет fraction_low = (# eigenvalues ≤ T_low) / N."""
    n_low = int(np.sum(eigenvalues <= T_low))
    return n_low / N if N > 0 else 0.0


def compute_n_low(eigenvalues: NDArray, T_low: float) -> int:
    """Вычисляет количество собственных чисел ≤ T_low."""
    return int(np.sum(eigenvalues <= T_low))


def compute_ipr_single(eigenvector: NDArray) -> float:
    """
    Вычисляет IPR (inverse participation ratio) для одного собственного вектора.
    IPR = sum(v^4) / (sum(v^2))^2
    Большой IPR → вектор локализован.
    """
    v_squared = eigenvector ** 2
    sum_v2 = np.sum(v_squared)
    sum_v4 = np.sum(eigenvector ** 4)
    
    if sum_v2 == 0:
        return 0.0
    
    return float(sum_v4 / (sum_v2 ** 2))


def compute_ipr_for_vectors(
    eigenvectors: NDArray,
    eigenvalues: NDArray,
    n_vectors: int,
    N: int
) -> List[IPRResultDTO]:
    """
    Вычисляет IPR для первых n_vectors собственных векторов.
    """
    # Порог для определения локализации: IPR > 1/sqrt(N) указывает на локализацию
    localization_threshold = 1.0 / np.sqrt(N) if N > 0 else 0.1
    
    result = []
    for i in range(min(n_vectors, eigenvectors.shape[1])):
        ipr = compute_ipr_single(eigenvectors[:, i])
        is_localized = ipr > localization_threshold
        
        result.append(IPRResultDTO(
            index=i,
            eigenvalue=float(eigenvalues[i]),
            ipr=ipr,
            is_localized=is_localized
        ))
    
    return result


def compute_degree_stats(matrix: NDArray) -> DegreeStatsDTO:
    """
    Вычисляет статистики степеней из диагонали матрицы Лапласа.
    В матрице Лапласа диагональные элементы равны степеням вершин.
    """
    degrees = np.diag(matrix)
    
    return DegreeStatsDTO(
        d_max=float(np.max(degrees)),
        d_avg=float(np.mean(degrees)),
        d_min=float(np.min(degrees))
    )


def compute_T_low_rel(lambda_max: float, alpha: float) -> float:
    """Вычисляет относительный порог T_low_rel = alpha * lambda_max."""
    return alpha * lambda_max


def compute_T_low(T_low_abs: float, T_low_rel: float, small_eps: float = 1e-10) -> float:
    """
    Выбирает порог низких частот.
    T_low = max(min(T_low_abs, T_low_rel), small_eps)
    """
    return max(min(T_low_abs, T_low_rel), small_eps)

