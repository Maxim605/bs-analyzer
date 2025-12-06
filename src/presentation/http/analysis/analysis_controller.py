from __future__ import annotations
import json
from fastapi import APIRouter, status, HTTPException, File, UploadFile, Form
from typing import Union, Optional

from src.application.analysis.queries.analyze_graph import AnalyzeGraphHandler
from src.application.analysis.dto.analysis_dto import (
    AnalysisRequestDTO,
    AdjacencyMatrixDTO,
    LaplacianMatrixDTO,
    EigenvaluesDTO,
    ChromaticNumberDTO,
    GraphStatsDTO
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

