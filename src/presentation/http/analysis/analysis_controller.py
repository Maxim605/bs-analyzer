from __future__ import annotations
import json
import time
import logging
from fastapi import APIRouter, status, HTTPException, File, UploadFile, Form
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
        response_model=Union[LaplacianMatrixDTO, str],
        status_code=status.HTTP_200_OK
    )
    async def get_laplacian_matrix(
        file: Optional[UploadFile] = File(None),
        graph_json: Optional[str] = Form(None),
        async_mode: Optional[bool] = Form(None)
    ):
        """Получить матрицу Лапласа графа."""
        try:
            dto = await _parse_request(file, graph_json, async_mode)
            return analysis_handler.get_laplacian_matrix(dto)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.post(
        "/eigenvalues",
        response_model=Union[EigenvaluesDTO, str],
        status_code=status.HTTP_200_OK
    )
    async def get_eigenvalues(
        file: Optional[UploadFile] = File(None),
        graph_json: Optional[str] = Form(None),
        async_mode: Optional[bool] = Form(None)
    ):
        """Получить собственные числа графа (спектр)."""
        try:
            dto = await _parse_request(file, graph_json, async_mode)
            return analysis_handler.get_eigenvalues(dto)
        except HTTPException:
            raise
        except Exception as e:
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

