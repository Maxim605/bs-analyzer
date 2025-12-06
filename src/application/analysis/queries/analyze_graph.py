from __future__ import annotations
from dataclasses import dataclass
import logging
from typing import Any

from src.domain.clusterizer.entities.graph import Graph, GraphNode, GraphLink
from src.domain.analysis.services.graph_analysis_service import GraphAnalysisService
from src.infrastructure.clusterizer.redis.redis_manager import RedisTaskManager
from src.application.analysis.dto.analysis_dto import (
    AnalysisRequestDTO, 
    AdjacencyMatrixDTO,
    LaplacianMatrixDTO,
    EigenvaluesDTO,
    ChromaticNumberDTO,
    GraphStatsDTO
)

logger = logging.getLogger(__name__)

@dataclass
class AnalyzeGraphHandler:
    """
    CQRS Query Handler: Обрабатывает запросы на анализ графа.
    """
    analysis_service: GraphAnalysisService
    redis_manager: RedisTaskManager

    def _create_graph(self, dto: AnalysisRequestDTO) -> Graph:
        nodes = [GraphNode(node_id=n.id, name=n.name, index=n.index) for n in dto.graph.nodes]
        links = [GraphLink(source=l.source, target=l.target) for l in dto.graph.links]
        return Graph(nodes=nodes, links=links)

    def _handle_async(self, dto: AnalysisRequestDTO, analysis_type: str) -> str:
        task_data = dto.model_dump()
        task_data['analysis_type'] = analysis_type
        task_id = self.redis_manager.enqueue_clustering_task(task_data) # Используем ту же очередь для простоты
        logger.info(f"Analysis task ({analysis_type}) enqueued: {task_id}")
        return f"Task accepted: {task_id}"

    def get_adjacency_matrix(self, dto: AnalysisRequestDTO) -> AdjacencyMatrixDTO | str:
        if dto.async_mode:
            return self._handle_async(dto, 'adjacency_matrix')
        
        graph = self._create_graph(dto)
        matrix = self.analysis_service.get_adjacency_matrix(graph)
        return AdjacencyMatrixDTO(matrix=matrix)

    def get_laplacian_matrix(self, dto: AnalysisRequestDTO) -> LaplacianMatrixDTO | str:
        if dto.async_mode:
            return self._handle_async(dto, 'laplacian_matrix')

        graph = self._create_graph(dto)
        matrix = self.analysis_service.get_laplacian_matrix(graph)
        return LaplacianMatrixDTO(matrix=matrix)

    def get_eigenvalues(self, dto: AnalysisRequestDTO) -> EigenvaluesDTO | str:
        if dto.async_mode:
            return self._handle_async(dto, 'eigenvalues')

        graph = self._create_graph(dto)
        values = self.analysis_service.get_eigenvalues(graph)
        return EigenvaluesDTO(values=values)

    def get_chromatic_number(self, dto: AnalysisRequestDTO) -> ChromaticNumberDTO | str:
        if dto.async_mode:
            return self._handle_async(dto, 'chromatic_number')

        graph = self._create_graph(dto)
        number = self.analysis_service.get_chromatic_number(graph)
        return ChromaticNumberDTO(chromatic_number=number)

    def get_basic_stats(self, dto: AnalysisRequestDTO) -> GraphStatsDTO | str:
        if dto.async_mode:
            return self._handle_async(dto, 'basic_stats')

        graph = self._create_graph(dto)
        stats = self.analysis_service.get_basic_stats(graph)
        return GraphStatsDTO(stats=stats)

