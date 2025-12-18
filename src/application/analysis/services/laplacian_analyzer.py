"""
Основной анализатор матрицы Лапласа.
"""
from __future__ import annotations
import logging
import numpy as np
from numpy.typing import NDArray

from src.application.analysis.dto.laplacian_analysis_dto import (
    LaplacianAnalysisParamsDTO,
    LaplacianAnalysisResponseDTO,
    ComputedConstantsDTO,
)
from src.application.analysis.services.laplacian_computations import (
    validate_matrix_square,
    validate_matrix_symmetric,
    validate_matrix_numeric,
    symmetrize_matrix,
    compute_spectrum,
    compute_n_vertices,
    compute_lambda_max,
    compute_lambda_min,
    compute_lambda_2,
    compute_n_zero,
    compute_eigengaps,
    compute_ipr_for_vectors,
    compute_degree_stats,
    compute_T_low_rel,
    compute_T_low,
)
from src.application.analysis.services.laplacian_assessments import (
    assess_connectivity,
    assess_low_frequencies,
    assess_localization,
    find_k_candidates,
    generate_summary,
    generate_recommendations,
)

logger = logging.getLogger(__name__)


class LaplacianAnalyzer:
    """Анализатор матрицы Лапласа по спектральным характеристикам."""
    
    def __init__(self, params: LaplacianAnalysisParamsDTO = None):
        self.params = params or LaplacianAnalysisParamsDTO()
    
    def validate_and_prepare_matrix(self, matrix: NDArray) -> NDArray:
        """
        Валидирует и подготавливает матрицу к анализу.
        """
        # Проверки
        validate_matrix_square(matrix)
        validate_matrix_numeric(matrix)
        
        # Проверяем симметричность, при необходимости симметризуем
        try:
            validate_matrix_symmetric(matrix)
        except ValueError:
            logger.warning("Матрица не симметрична, выполняется симметризация")
            matrix = symmetrize_matrix(matrix)
        
        return matrix
    
    def analyze(self, matrix: NDArray) -> LaplacianAnalysisResponseDTO:
        """
        Выполняет полный анализ матрицы Лапласа.
        """
        logger.info(f"Начало анализа матрицы Лапласа размера {matrix.shape}")
        
        # 1. Предобработка
        matrix = self.validate_and_prepare_matrix(matrix)
        
        # 2. Вычисление спектра
        eigenvalues, eigenvectors = compute_spectrum(matrix)
        
        # 3. Базовые константы
        N = compute_n_vertices(matrix)
        lambda_max = compute_lambda_max(eigenvalues)
        lambda_min = compute_lambda_min(eigenvalues)
        lambda_2 = compute_lambda_2(eigenvalues)
        n_zero = compute_n_zero(eigenvalues, self.params.zero_tol)
        
        # 4. Eigengaps
        eigengaps = compute_eigengaps(eigenvalues, self.params, lambda_max)
        
        # 5. Статистики степеней
        degree_stats = compute_degree_stats(matrix)
        
        # 6. Пороги низких частот
        T_low_rel = compute_T_low_rel(lambda_max, self.params.alpha)
        T_low_used = compute_T_low(self.params.T_low_abs, T_low_rel)
        
        # 7. IPR для собственных векторов
        # Анализируем первые max_k_search векторов
        k_for_ipr = min(self.params.max_k_search, N)
        ipr_results = compute_ipr_for_vectors(eigenvectors, eigenvalues, k_for_ipr, N)
        
        # 8. Оценки
        connectivity_assessment = assess_connectivity(n_zero, lambda_2, lambda_max, self.params)
        
        low_frequency_assessment = assess_low_frequencies(
            eigenvalues, T_low_rel, T_low_used, N, self.params
        )
        
        localization_assessment = assess_localization(ipr_results, k_for_ipr)
        
        # 9. Поиск кандидатов k
        k_candidates = find_k_candidates(eigengaps, n_zero, self.params)
        
        # 10. Генерация резюме и рекомендаций
        summary = generate_summary(
            N, n_zero, lambda_2, lambda_max,
            low_frequency_assessment.fraction_low, k_candidates
        )
        
        recommendations = generate_recommendations(
            connectivity_assessment,
            low_frequency_assessment,
            localization_assessment,
            k_candidates
        )
        
        # Формируем результат
        computed_constants = ComputedConstantsDTO(
            N=N,
            lambda_max=lambda_max,
            lambda_min=lambda_min,
            lambda_2=lambda_2,
            n_zero=n_zero,
            eigenvalues=eigenvalues.tolist(),
            eigengaps=eigengaps,
            degree_stats=degree_stats
        )
        
        logger.info(f"Анализ завершён. N={N}, n_zero={n_zero}, k_candidates={[k.k for k in k_candidates]}")
        
        return LaplacianAnalysisResponseDTO(
            params=self.params,
            computed_constants=computed_constants,
            connectivity_assessment=connectivity_assessment,
            low_frequency_assessment=low_frequency_assessment,
            localization_assessment=localization_assessment,
            k_candidates=k_candidates,
            summary=summary,
            recommendations=recommendations
        )

