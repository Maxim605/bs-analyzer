from __future__ import annotations
from dataclasses import dataclass
import logging
import time
from typing import Any, Optional, List

from src.domain.clusterizer.entities.graph import Graph, GraphNode, GraphLink
from src.domain.analysis.services.graph_analysis_service import GraphAnalysisService
from src.domain.clusterizer.services.clustering_strategy import ClusteringStrategy
from src.infrastructure.clusterizer.redis.redis_manager import RedisTaskManager
from src.application.analysis.dto.analysis_dto import (
    AnalysisRequestDTO, 
    AdjacencyMatrixDTO,
    LaplacianMatrixDTO,
    EigenvaluesDTO,
    ChromaticNumberDTO,
    GraphStatsDTO,
    OptimalClusterRequestDTO,
    OptimalClusterResponseDTO,
    EpochStatsDTO
)
from src.application.clusterizer.dto.graph_dto import NodeDTO, LinkDTO

logger = logging.getLogger(__name__)

@dataclass
class AnalyzeGraphHandler:
    """
    CQRS Query Handler: Обрабатывает запросы на анализ графа.
    """
    analysis_service: GraphAnalysisService
    redis_manager: RedisTaskManager
    clustering_strategy: Optional[ClusteringStrategy] = None

    def _create_graph(self, dto: AnalysisRequestDTO) -> Graph:
        nodes = [GraphNode(node_id=n.id, name=n.name, index=n.index) for n in dto.graph.nodes]
        links = [GraphLink(source=l.source, target=l.target) for l in dto.graph.links]
        return Graph(nodes=nodes, links=links)

    def _handle_async(self, dto: AnalysisRequestDTO, analysis_type: str) -> str:
        task_data = dto.model_dump()
        task_data['analysis_type'] = analysis_type
        task_id = self.redis_manager.enqueue_clustering_task(task_data) # Используем ту же очередь для простоты
        logger.info(f"Analysis task ({analysis_type}) enqueued: {task_id}")
        return task_id

    def find_optimal_clusters(self, dto: OptimalClusterRequestDTO) -> OptimalClusterResponseDTO | str:
        if dto.async_mode:
            # Для async режима: выполняем задачу синхронно и сохраняем результат
            # В реальном приложении это делал бы воркер
            task_id = self._handle_async(dto, 'optimal_clusters')
            # Выполняем задачу и сохраняем результат
            result = self._find_optimal_clusters_sync(dto)
            # Сохраняем результат в Redis
            self.redis_manager.save_task_result(task_id, result.model_dump())
            return task_id
        
        return self._find_optimal_clusters_sync(dto)

    def _find_optimal_clusters_sync(self, dto: OptimalClusterRequestDTO) -> OptimalClusterResponseDTO:
        """Синхронное выполнение поиска оптимальных кластеров."""
        start_time = time.time()
        
        if not self.clustering_strategy:
            raise ValueError("Clustering strategy is not configured in AnalyzeGraphHandler")

        graph = self._create_graph(dto)
        epoch_stats = []
        
        best_k = dto.min_k
        best_modularity = -1.0
        best_graph_snapshot = None
        best_stats = {}

        # Если граф очень маленький, корректируем max_k
        max_k = min(dto.max_k, len(graph.nodes))
        min_k = min(dto.min_k, max_k)
        
        total_iterations = max_k - min_k + 1
        logger.info(f"Starting optimal clusters search: min_k={min_k}, max_k={max_k}, total_iterations={total_iterations}, nodes={len(graph.nodes)}, edges={len(graph.links)}")

        for iteration, k in enumerate(range(min_k, max_k + 1), start=1):
            iteration_start = time.time()
            
            # Клонируем граф или сбрасываем кластеры, но здесь assign_clusters перезапишет
            labels = self.clustering_strategy.clusterize(graph, n_clusters=k)
            graph.assign_clusters(labels)
            
            modularity = self.analysis_service.get_modularity(graph)
            stats = self.analysis_service.get_basic_stats(graph)
            
            epoch_stats.append(EpochStatsDTO(
                k=k,
                modularity=modularity,
                stats=stats
            ))
            
            # Вычисляем процент выполнения
            progress_percent = (iteration / total_iterations) * 100
            iteration_time = time.time() - iteration_start
            elapsed_time = time.time() - start_time
            
            logger.info(
                f"Progress: {progress_percent:.1f}% | "
                f"Iteration {iteration}/{total_iterations} (k={k}) | "
                f"Modularity: {modularity:.4f} | "
                f"Iteration time: {iteration_time:.2f}s | "
                f"Total elapsed: {elapsed_time:.2f}s"
            )
            
            if modularity > best_modularity:
                best_modularity = modularity
                best_k = k
                best_stats = stats
                
                # Создаем snapshot графа для лучшего результата
                response_nodes = [
                    NodeDTO(
                        id=n.node_id,
                        name=n.name,
                        index=n.index,
                        cluster=n.cluster.value if n.cluster else None
                    ) for n in graph.nodes
                ]
                response_links = [LinkDTO(source=l.source, target=l.target) for l in graph.links]
                best_graph_snapshot = {
                    'nodes': [n.model_dump() for n in response_nodes],
                    'links': [l.model_dump() for l in response_links]
                }
                logger.info(f"New best result found: k={best_k}, modularity={best_modularity:.4f}")

        if best_graph_snapshot is None:
             # Fallback если цикл не выполнился или что-то пошло не так
             best_graph_snapshot = {'nodes': [], 'links': []}

        total_time = time.time() - start_time
        logger.info(
            f"Optimal clusters search completed | "
            f"Optimal k: {best_k} | "
            f"Best modularity: {best_modularity:.4f} | "
            f"Total processing time: {total_time:.2f}s"
        )

        return OptimalClusterResponseDTO(
            optimal_k=best_k,
            best_stats=best_stats,
            clustered_graph=best_graph_snapshot,
            epoch_stats=epoch_stats
        )

    def get_optimal_clusters_result(self, task_id: str) -> OptimalClusterResponseDTO | None:
        """
        Получает результат задачи поиска оптимальных кластеров по task_id.
        """
        result = self.redis_manager.get_task_result(task_id)
        if result is None:
            return None
        
        # Преобразуем словарь обратно в DTO
        try:
            return OptimalClusterResponseDTO(**result)
        except Exception as e:
            logger.error(f"Error parsing task result for {task_id}: {e}")
            return None

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

