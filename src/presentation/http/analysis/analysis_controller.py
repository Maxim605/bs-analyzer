from __future__ import annotations
import json
import time
import logging
from pathlib import Path
from fastapi import APIRouter, status, HTTPException, File, UploadFile, Form
from fastapi.responses import Response, FileResponse
from typing import Union, Optional

logger = logging.getLogger(__name__)

from src.application.analysis.queries.analyze_graph import AnalyzeGraphHandler
from src.application.analysis.dto.analysis_dto import (
    AnalysisRequestDTO,
    AdjacencyMatrixDTO,
    LaplacianMatrixDTO,
    EigenvaluesDTO,
    ChromaticNumberDTO,
    GraphStatsDTO,
    OptimalClusterRequestDTO,
    OptimalClusterResponseDTO,
    LibraryOptimalClusterResponseDTO
)
from src.application.analysis.dto.laplacian_analysis_dto import (
    LaplacianAnalysisParamsDTO,
    LaplacianAnalysisResponseDTO
)

def create_analysis_router(
    analysis_handler: AnalyzeGraphHandler
) -> APIRouter:
    """
    Создает роутер модуля Analysis.
    """
    router = APIRouter(prefix="/analysis", tags=["analysis"])

    async def _parse_request(
        file: Optional[UploadFile] = File(None),
        graph_json: Optional[str] = Form(None),
        async_mode: Optional[bool] = Form(None)
    ) -> AnalysisRequestDTO:
        """
        Парсит запрос: если передан файл, использует его, иначе использует JSON из параметров.
        """
        if file is not None:
            # Если файл передан, читаем его содержимое
            content = await file.read()
            try:
                data = json.loads(content.decode('utf-8'))
            except json.JSONDecodeError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Неверный формат JSON в файле: {str(e)}"
                )
        elif graph_json is not None:
            # Если файла нет, используем JSON из параметров
            try:
                data = json.loads(graph_json)
            except json.JSONDecodeError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Неверный формат JSON в параметре graph_json: {str(e)}"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Необходимо передать либо файл, либо параметр graph_json"
            )
        
        # Формируем правильную структуру для AnalysisRequestDTO
        # Если в данных есть nodes и links на верхнем уровне, оборачиваем их в graph
        if 'graph' not in data and ('nodes' in data or 'links' in data):
            # Определяем async_mode: приоритет у Form параметра, затем из JSON, затем False
            final_async_mode = async_mode if async_mode is not None else data.get('async_mode', False)
            data = {
                'graph': {
                    'nodes': data.get('nodes', []),
                    'links': data.get('links', [])
                },
                'async_mode': final_async_mode
            }
        else:
            # Если уже есть graph, используем его
            # async_mode: приоритет у Form параметра, затем из JSON, затем False
            if async_mode is not None:
                data['async_mode'] = async_mode
            elif 'async_mode' not in data:
                data['async_mode'] = False
        
        return AnalysisRequestDTO(**data)

    async def _parse_optimal_request(
        file: Optional[UploadFile] = File(None),
        graph_json: Optional[str] = Form(None),
        async_mode: Optional[bool] = Form(None),
        min_k: int = Form(2),
        max_k: int = Form(10)
    ) -> OptimalClusterRequestDTO:
        """
        Парсит запрос для поиска оптимальных кластеров с поддержкой min_k и max_k.
        """
        # Используем базовый парсер для получения данных графа
        base_dto = await _parse_request(file, graph_json, async_mode)
        
        # Получаем данные графа как словарь
        graph_data = base_dto.graph
        
        # Формируем DTO для поиска оптимальных кластеров
        return OptimalClusterRequestDTO(
            graph=graph_data,
            async_mode=base_dto.async_mode,
            min_k=min_k,
            max_k=max_k
        )

    @router.post(
        "/optimal-clusters",
        response_model=Union[OptimalClusterResponseDTO, str],
        status_code=status.HTTP_200_OK
    )
    async def find_optimal_clusters(
        file: Optional[UploadFile] = File(None),
        graph_json: Optional[str] = Form(None),
        async_mode: Optional[bool] = Form(None),
        min_k: int = Form(2),
        max_k: int = Form(10)
    ):
        """
        Найти оптимальное количество кластеров (спектральная кластеризация).
        Оценивает качество разбиения с помощью модулярности и возвращает статистики для каждой эпохи.
        В async режиме возвращает task_id, результат можно получить через GET /analysis/optimal-clusters/{task_id}
        """
        request_start_time = time.time()
        try:
            logger.info(f"Received optimal clusters request: min_k={min_k}, max_k={max_k}, async_mode={async_mode}")
            dto = await _parse_optimal_request(file, graph_json, async_mode, min_k, max_k)
            result = analysis_handler.find_optimal_clusters(dto)
            
            request_time = time.time() - request_start_time
            logger.info(
                f"Optimal clusters request completed | "
                f"Request processing time: {request_time:.2f}s | "
                f"Result type: {type(result).__name__}"
            )
            
            return result
        except HTTPException:
            request_time = time.time() - request_start_time
            logger.warning(f"Optimal clusters request failed after {request_time:.2f}s")
            raise
        except Exception as e:
            request_time = time.time() - request_start_time
            logger.error(f"Optimal clusters request error after {request_time:.2f}s: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.post(
        "/optimal-clusters-library",
        response_model=Union[LibraryOptimalClusterResponseDTO, str],
        status_code=status.HTTP_200_OK
    )
    async def find_optimal_clusters_library(
        file: Optional[UploadFile] = File(None),
        graph_json: Optional[str] = Form(None),
        async_mode: Optional[bool] = Form(None),
        min_k: int = Form(2),
        max_k: int = Form(10)
    ):
        """
        Найти оптимальное количество кластеров используя библиотечные метрики scikit-learn:
        - Silhouette Score (чем выше, тем лучше) - основной метод
        - Calinski-Harabasz Index (чем выше, тем лучше)
        - Davies-Bouldin Index (чем ниже, тем лучше)
        
        Возвращает оптимальное k на основе Silhouette Score и все метрики для каждого k.
        """
        request_start_time = time.time()
        try:
            logger.info(f"Received library-based optimal clusters request: min_k={min_k}, max_k={max_k}, async_mode={async_mode}")
            dto = await _parse_optimal_request(file, graph_json, async_mode, min_k, max_k)
            result = analysis_handler.find_optimal_clusters_library(dto)
            
            request_time = time.time() - request_start_time
            logger.info(
                f"Library-based optimal clusters request completed | "
                f"Request processing time: {request_time:.2f}s | "
                f"Result type: {type(result).__name__}"
            )
            
            return result
        except HTTPException:
            request_time = time.time() - request_start_time
            logger.warning(f"Library-based optimal clusters request failed after {request_time:.2f}s")
            raise
        except Exception as e:
            request_time = time.time() - request_start_time
            logger.error(f"Library-based optimal clusters request error after {request_time:.2f}s: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get(
        "/optimal-clusters/{task_id}",
        response_model=OptimalClusterResponseDTO,
        status_code=status.HTTP_200_OK
    )
    def get_optimal_clusters_result(task_id: str):
        """
        Получить результат задачи поиска оптимальных кластеров по task_id.
        """
        request_start_time = time.time()
        try:
            logger.info(f"Retrieving optimal clusters result for task_id: {task_id}")
            result = analysis_handler.get_optimal_clusters_result(task_id)
            if result is None:
                request_time = time.time() - request_start_time
                logger.warning(f"Task {task_id} not found (request time: {request_time:.2f}s)")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Task {task_id} not found or not completed yet"
                )
            
            request_time = time.time() - request_start_time
            logger.info(
                f"Task result retrieved successfully | "
                f"Task ID: {task_id} | "
                f"Optimal k: {result.optimal_k} | "
                f"Request time: {request_time:.2f}s"
            )
            return result
        except HTTPException:
            raise
        except Exception as e:
            request_time = time.time() - request_start_time
            logger.error(f"Error retrieving task result for {task_id} after {request_time:.2f}s: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.post(
        "/adjacency-matrix",
        response_model=Union[AdjacencyMatrixDTO, str],
        status_code=status.HTTP_200_OK
    )
    async def get_adjacency_matrix(
        file: Optional[UploadFile] = File(None),
        graph_json: Optional[str] = Form(None),
        async_mode: Optional[bool] = Form(None)
    ):
        """Получить матрицу смежности графа."""
        try:
            dto = await _parse_request(file, graph_json, async_mode)
            return analysis_handler.get_adjacency_matrix(dto)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.post(
        "/laplacian-matrix",
        status_code=status.HTTP_200_OK
    )
    async def get_laplacian_matrix(
        file: Optional[UploadFile] = File(None),
        graph_json: Optional[str] = Form(None),
        async_mode: Optional[bool] = Form(False)
    ):
        """
        Получить матрицу Лапласа графа в формате Excel.
        В Excel файле id вершин указаны в заголовках строк и столбцов.
        """
        try:
            dto = await _parse_request(file, graph_json, async_mode)
            result = analysis_handler.get_laplacian_matrix(dto)
            
            # Если async_mode, возвращаем task_id как строку
            if isinstance(result, str):
                return result
            
            # Иначе возвращаем Excel файл
            return Response(
                content=result,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={
                    "Content-Disposition": "attachment; filename=laplacian_matrix.xlsx"
                }
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.post(
        "/eigenvalues",
        status_code=status.HTTP_200_OK
    )
    async def get_eigenvalues(
        laplacian_matrix_file: Optional[UploadFile] = File(None),
        async_mode: Optional[bool] = Form(False),
        sort: Optional[str] = Form("-")
    ):
        """
        Получить собственные числа из матрицы Лапласа в формате Excel.
        Принимает xlsx файл с матрицей Лапласа (результат /analysis/laplacian-matrix).
        Возвращает xlsx файл с собственными числами.
        Перед вычислением проверяет, что матрица симметричная и сумма всех элементов равна 0.
        
        Параметры:
        - sort: режим сортировки ("-" для убывания, "+" для возрастания). По умолчанию "-".
        """
        try:
            if async_mode:
                # Для async режима используем старый способ с графом
                # Но это не поддерживается для Excel файлов
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Async режим не поддерживается для Excel файлов"
                )
            
            if laplacian_matrix_file is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Необходимо передать xlsx файл с матрицей Лапласа"
                )
            
            # Проверяем тип файла
            if not laplacian_matrix_file.filename.endswith('.xlsx'):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Файл должен быть в формате .xlsx"
                )
            
            # Проверяем параметр сортировки
            if sort not in ["-", "+"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Параметр sort должен быть '-' (убывание) или '+' (возрастание)"
                )
            
            # Читаем содержимое файла
            excel_bytes = await laplacian_matrix_file.read()
            
            # Вычисляем собственные числа
            result = analysis_handler.get_eigenvalues_from_excel(excel_bytes, sort=sort)
            
            # Возвращаем Excel файл
            return Response(
                content=result,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={
                    "Content-Disposition": "attachment; filename=eigenvalues.xlsx"
                }
            )
        except HTTPException:
            raise
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            logger.error(f"Error computing eigenvalues: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.post(
        "/eigenvectors",
        status_code=status.HTTP_200_OK
    )
    async def get_eigenvectors(
        laplacian_matrix_file: Optional[UploadFile] = File(None),
        async_mode: Optional[bool] = Form(False),
        sort: Optional[str] = Form("+")
    ):
        """
        Получить собственные векторы из матрицы Лапласа в формате Excel.
        
        Принимает xlsx файл с матрицей Лапласа (результат /analysis/laplacian-matrix).
        Возвращает xlsx файл с собственными векторами.
        
        **Применение в спектральной кластеризации:**
        Собственные векторы матрицы Лапласа используются для построения спектрального вложения (spectral embedding).
        Первые k собственных векторов (соответствующих наименьшим собственным числам) формируют низкоразмерное 
        представление вершин графа, в котором кластеры становятся более разделимыми. Это позволяет применять 
        стандартные алгоритмы кластеризации (например, k-means) в этом новом пространстве для получения 
        более качественных результатов, чем при работе напрямую с исходным графом.
        
        Каждый столбец в результате представляет один собственный вектор, упорядоченный по возрастанию 
        соответствующих собственных чисел. Первые векторы (v_1, v_2, ..., v_k) обычно используются для 
        спектральной кластеризации, так как они соответствуют глобальной структуре графа.
        
        Перед вычислением проверяет, что матрица симметричная и сумма всех элементов равна 0.
        
        Параметры:
        - sort: режим сортировки ("-" для убывания, "+" для возрастания). По умолчанию "+" (рекомендуется для спектральной кластеризации).
        """
        try:
            if async_mode:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Async режим не поддерживается для Excel файлов"
                )
            
            if laplacian_matrix_file is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Необходимо передать xlsx файл с матрицей Лапласа"
                )
            
            # Проверяем тип файла
            if not laplacian_matrix_file.filename.endswith('.xlsx'):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Файл должен быть в формате .xlsx"
                )
            
            # Проверяем параметр сортировки
            if sort not in ["-", "+"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Параметр sort должен быть '-' (убывание) или '+' (возрастание)"
                )
            
            # Читаем содержимое файла
            excel_bytes = await laplacian_matrix_file.read()
            
            # Вычисляем собственные векторы
            result = analysis_handler.get_eigenvectors_from_excel(excel_bytes, sort=sort)
            
            # Возвращаем Excel файл
            return Response(
                content=result,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={
                    "Content-Disposition": "attachment; filename=eigenvectors.xlsx"
                }
            )
        except HTTPException:
            raise
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            logger.error(f"Error computing eigenvectors: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.post(
        "/eigengaps",
        status_code=status.HTTP_200_OK
    )
    async def get_eigengaps(
        laplacian_matrix_file: Optional[UploadFile] = File(None),
        async_mode: Optional[bool] = Form(False),
        sort: Optional[str] = Form("+")
    ):
        """
        Получить eigengaps (разности между соседними собственными числами) из матрицы Лапласа в формате Excel.
        
        Принимает xlsx файл с матрицей Лапласа (результат /analysis/laplacian-matrix).
        Возвращает xlsx файл с eigengaps: g_i = λ_{i+1} - λ_i.
        
        **Применение в спектральной кластеризации:**
        Eigengaps используются для определения оптимального количества кластеров k. Большие разности между 
        соседними собственными числами указывают на естественные границы между кластерами. 
        
        Метод основан на наблюдении, что если граф имеет k хорошо разделённых кластеров, то первые k 
        собственных чисел будут малыми (близкими к нулю), а разность между λ_k и λ_{k+1} будет значительной.
        Таким образом, анализ eigengaps позволяет автоматически выбрать количество кластеров без необходимости 
        перебора различных значений k и оценки качества кластеризации.
        
        В результате для каждого gap указывается:
        - Gap Index: индекс разности (i)
        - λ_i: i-е собственное число
        - λ_{i+1}: (i+1)-е собственное число
        - Gap: разность λ_{i+1} - λ_i
        
        Значимые gaps (большие значения) обычно соответствуют оптимальному количеству кластеров. 
        Рекомендуется искать локальные максимумы в последовательности gaps, особенно среди первых 
        10-50% собственных чисел (низкочастотная часть спектра).
        
        Перед вычислением проверяет, что матрица симметричная и сумма всех элементов равна 0.
        
        Параметры:
        - sort: режим сортировки ("-" для убывания, "+" для возрастания). По умолчанию "+" (рекомендуется для анализа gaps).
        """
        try:
            if async_mode:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Async режим не поддерживается для Excel файлов"
                )
            
            if laplacian_matrix_file is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Необходимо передать xlsx файл с матрицей Лапласа"
                )
            
            # Проверяем тип файла
            if not laplacian_matrix_file.filename.endswith('.xlsx'):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Файл должен быть в формате .xlsx"
                )
            
            # Проверяем параметр сортировки
            if sort not in ["-", "+"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Параметр sort должен быть '-' (убывание) или '+' (возрастание)"
                )
            
            # Читаем содержимое файла
            excel_bytes = await laplacian_matrix_file.read()
            
            # Вычисляем eigengaps
            result = analysis_handler.get_eigengaps_from_excel(excel_bytes, sort=sort)
            
            # Возвращаем Excel файл
            return Response(
                content=result,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={
                    "Content-Disposition": "attachment; filename=eigengaps.xlsx"
                }
            )
        except HTTPException:
            raise
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            logger.error(f"Error computing eigengaps: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get(
        "/laplacian-analysis/algorithm",
        status_code=status.HTTP_200_OK
    )
    def get_laplacian_analysis_algorithm():
        """
        Скачать описание алгоритма анализа матрицы Лапласа.
        
        Возвращает markdown файл с подробным описанием алгоритма, включая:
        - Этапы обработки матрицы
        - Вычисляемые константы
        - Методы оценок
        - Интерпретацию результатов
        - Рекомендации по использованию
        """
        try:
            # Путь к файлу с описанием алгоритма
            algorithm_file = Path(__file__).parent.parent.parent.parent / "docs" / "laplacian_analysis_algorithm.md"
            
            if not algorithm_file.exists():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Файл с описанием алгоритма не найден"
                )
            
            return FileResponse(
                path=str(algorithm_file),
                media_type="text/markdown",
                filename="laplacian_analysis_algorithm.md",
                headers={
                    "Content-Disposition": "attachment; filename=laplacian_analysis_algorithm.md"
                }
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error serving algorithm file: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.post(
        "/laplacian-analysis",
        response_model=LaplacianAnalysisResponseDTO,
        status_code=status.HTTP_200_OK
    )
    async def analyze_laplacian(
        laplacian_matrix_file: UploadFile = File(...),
        async_mode: Optional[bool] = Form(False),
        zero_tol: Optional[float] = Form(1e-8),
        T_low_abs: Optional[float] = Form(2.0),
        alpha: Optional[float] = Form(0.02),
        gap_factor: Optional[float] = Form(3.0),
        gap_ratio: Optional[float] = Form(1.5),
        frac_many_thresh: Optional[float] = Form(0.2),
        k_search_fraction: Optional[float] = Form(0.5),
        max_k_search: Optional[int] = Form(50)
    ):
        """
        Выполняет полный анализ матрицы Лапласа по спектральным характеристикам.
        
        Принимает xlsx файл с матрицей Лапласа и возвращает:
        - Вычисленные константы (N, λ_max, λ_2, n_zero, eigengaps и т.д.)
        - Оценку связности графа
        - Оценку низкочастотной части спектра
        - Оценку локализации собственных векторов
        - Кандидатов для количества кластеров k
        - Рекомендации по дальнейшему анализу
        
        **Описание алгоритма**: Для получения подробного описания алгоритма скачайте файл по адресу: `GET /analysis/laplacian-analysis/algorithm`
        
        Параметры:
        - zero_tol: допустимая погрешность для определения нуля (default: 1e-8)
        - T_low_abs: абсолютный порог низкой частоты (default: 2.0)
        - alpha: коэффициент для T_low_rel = alpha * lambda_max (default: 0.02)
        - gap_factor: множитель для определения значимого eigengap (default: 3.0)
        - gap_ratio: соотношение для значимости eigengap (default: 1.5)
        - frac_many_thresh: порог доли малых λ для оценки 'много' (default: 0.2)
        - k_search_fraction: доля спектра для поиска eigengaps (default: 0.5)
        - max_k_search: максимальное количество eigengaps для поиска (default: 50)
        """
        request_start_time = time.time()
        try:
            if async_mode:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Async режим не поддерживается для анализа Лапласа"
                )
            
            if laplacian_matrix_file is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Необходимо передать xlsx файл с матрицей Лапласа"
                )
            
            # Проверяем тип файла
            if not laplacian_matrix_file.filename.endswith('.xlsx'):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Файл должен быть в формате .xlsx"
                )
            
            # Формируем параметры анализа
            params = LaplacianAnalysisParamsDTO(
                zero_tol=zero_tol,
                T_low_abs=T_low_abs,
                alpha=alpha,
                gap_factor=gap_factor,
                gap_ratio=gap_ratio,
                frac_many_thresh=frac_many_thresh,
                k_search_fraction=k_search_fraction,
                max_k_search=max_k_search
            )
            
            logger.info(f"Received laplacian analysis request with params: {params}")
            
            # Читаем содержимое файла
            excel_bytes = await laplacian_matrix_file.read()
            
            # Выполняем анализ
            result = analysis_handler.analyze_laplacian_from_excel(excel_bytes, params)
            
            request_time = time.time() - request_start_time
            logger.info(
                f"Laplacian analysis completed | "
                f"N={result.computed_constants.N} | "
                f"k_candidates={[k.k for k in result.k_candidates]} | "
                f"Request time: {request_time:.2f}s"
            )
            
            return result
            
        except HTTPException:
            raise
        except ValueError as e:
            request_time = time.time() - request_start_time
            logger.warning(f"Laplacian analysis validation error after {request_time:.2f}s: {str(e)}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            request_time = time.time() - request_start_time
            logger.error(f"Laplacian analysis error after {request_time:.2f}s: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.post(
        "/chromatic-number",
        response_model=Union[ChromaticNumberDTO, str],
        status_code=status.HTTP_200_OK
    )
    async def get_chromatic_number(
        file: Optional[UploadFile] = File(None),
        graph_json: Optional[str] = Form(None),
        async_mode: Optional[bool] = Form(None)
    ):
        """Получить хроматическое число графа (приблизительное)."""
        try:
            dto = await _parse_request(file, graph_json, async_mode)
            return analysis_handler.get_chromatic_number(dto)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.post(
        "/stats",
        response_model=Union[GraphStatsDTO, str],
        status_code=status.HTTP_200_OK
    )
    async def get_basic_stats(
        file: Optional[UploadFile] = File(None),
        graph_json: Optional[str] = Form(None),
        async_mode: Optional[bool] = Form(None)
    ):
        """Получить основные характеристики графа."""
        try:
            dto = await _parse_request(file, graph_json, async_mode)
            return analysis_handler.get_basic_stats(dto)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    return router

