from __future__ import annotations
from fastapi import APIRouter, status, HTTPException, UploadFile, File, Header, BackgroundTasks
from fastapi.responses import FileResponse
from typing import Union, Optional
import json
import tempfile
import os

from src.application.clusterizer.commands.cluster_graph import ClusterGraphHandler
from src.application.clusterizer.dto.graph_dto import (
    ClusterizationRequestDTO, 
    ClusteredGraphDTO,
    GraphSourceDTO
)

def create_clusterizer_router(
    cluster_handler: ClusterGraphHandler
) -> APIRouter:
    """
    Создает роутер модуля Clusterizer.
    """
    router = APIRouter(prefix="/clusterizer", tags=["clusterizer"])

    @router.post(
        "/spectral-clusterize", 
        response_model=Union[ClusteredGraphDTO, str], # str для async task id
        status_code=status.HTTP_200_OK
    )
    def spectral_clusterize_graph(dto: ClusterizationRequestDTO):
        """
        POST /clusterizer/spectral-clusterize
        Спектральная кластеризация графа.
        Принимает граф в JSON теле запроса, возвращает граф с кластерами.
        """
        try:
            result = cluster_handler.execute(dto)
            return result
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail=str(e)
            )

    @router.post(
        "/spectral-clusterize-file",
        status_code=status.HTTP_200_OK
    )
    async def spectral_clusterize_graph_file(
        background_tasks: BackgroundTasks,
        file: UploadFile = File(..., description="JSON файл с графом"),
        x_cluster_count: Optional[str] = Header(None, description="Количество кластеров (n_clusters)"),
        x_async_mode: Optional[str] = Header(None, description="Асинхронный режим: 'true' или 'false'"),
        x_user_id: Optional[str] = Header(None, description="ID пользователя"),
        x_request_id: Optional[str] = Header(None, description="ID запроса для трейсинга")
    ):
        """
        POST /clusterizer/spectral-clusterize-file
        Спектральная кластеризация графа из файла.
        Принимает JSON файл с графом и параметры в заголовках.
        Возвращает JSON файл с результатами кластеризации.
        
        Headers:
        - X-Cluster-Count: количество кластеров (по умолчанию 5)
        - X-Async-Mode: 'true' для асинхронного режима, 'false' для синхронного (по умолчанию false)
        - X-User-Id: ID пользователя (опционально)
        - X-Request-Id: ID запроса для трейсинга (опционально)
        """
        temp_file = None
        try:
            # Валидация файла
            if not file.filename or not file.filename.endswith('.json'):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="File must be a JSON file (.json extension required)"
                )

            # Чтение и парсинг файла
            content = await file.read()
            try:
                graph_data = json.loads(content.decode('utf-8'))
            except json.JSONDecodeError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid JSON format: {str(e)}"
                )

            # Парсинг параметров из заголовков
            n_clusters = 5
            if x_cluster_count:
                try:
                    n_clusters = int(x_cluster_count)
                    if n_clusters < 2:
                        raise ValueError("n_clusters must be >= 2")
                except ValueError as e:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid X-Cluster-Count header: {str(e)}"
                    )

            async_mode = False
            if x_async_mode:
                async_mode = x_async_mode.lower() == 'true'

            # Валидация структуры графа
            if 'nodes' not in graph_data or 'links' not in graph_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Graph must contain 'nodes' and 'links' fields"
                )

            # Создание DTO из данных файла
            graph_dto = GraphSourceDTO(**graph_data)
            request_dto = ClusterizationRequestDTO(
                graph=graph_dto,
                n_clusters=n_clusters,
                async_mode=async_mode
            )

            # Выполнение кластеризации
            result = cluster_handler.execute(request_dto)
            
            # Если асинхронный режим, возвращаем JSON с task_id
            if isinstance(result, str):
                response_data = {"task_id": result, "status": "accepted"}
                temp_file = tempfile.NamedTemporaryFile(
                    mode='w', 
                    suffix='.json', 
                    delete=False,
                    encoding='utf-8'
                )
                json.dump(response_data, temp_file, ensure_ascii=False, indent=2)
                temp_file_path = temp_file.name
                temp_file.close()
                
                # Добавляем задачу на удаление файла после отправки
                background_tasks.add_task(os.unlink, temp_file_path)
                
                return FileResponse(
                    temp_file_path,
                    media_type='application/json',
                    filename='clustering_task.json'
                )
            
            # Синхронный режим - возвращаем файл с результатами
            if isinstance(result, ClusteredGraphDTO):
                # Создаем временный файл с результатами
                temp_file = tempfile.NamedTemporaryFile(
                    mode='w', 
                    suffix='.json', 
                    delete=False,
                    encoding='utf-8'
                )
                
                # Преобразуем DTO в словарь для JSON
                result_dict = {
                    "nodes": [node.model_dump() for node in result.nodes],
                    "links": [link.model_dump() for link in result.links],
                    "clusters_found": result.clusters_found
                }
                
                json.dump(result_dict, temp_file, ensure_ascii=False, indent=2)
                temp_file_path = temp_file.name
                temp_file.close()
                
                # Определяем имя файла для ответа
                input_filename = file.filename or 'graph.json'
                output_filename = f"clustered_{input_filename}"
                
                # Добавляем задачу на удаление файла после отправки
                background_tasks.add_task(os.unlink, temp_file_path)
                
                return FileResponse(
                    temp_file_path,
                    media_type='application/json',
                    filename=output_filename
                )
            
            # Неожиданный тип результата
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unexpected result type from clustering handler"
            )

        except HTTPException:
            if temp_file and os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
            raise
        except Exception as e:
            if temp_file and os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )

    return router

