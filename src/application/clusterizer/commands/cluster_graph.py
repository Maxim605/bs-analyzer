from __future__ import annotations
from dataclasses import dataclass
import logging

from src.domain.clusterizer.entities.graph import Graph, GraphNode, GraphLink
from src.domain.clusterizer.services.clustering_strategy import ClusteringStrategy
from src.application.clusterizer.dto.graph_dto import (
    ClusterizationRequestDTO, 
    ClusteredGraphDTO, 
    NodeDTO, 
    LinkDTO
)
from src.infrastructure.clusterizer.redis.redis_manager import RedisTaskManager

logger = logging.getLogger(__name__)

@dataclass
class ClusterGraphHandler:
    """
    CQRS Command Handler: Обрабатывает команду кластеризации графа.
    """
    clustering_strategy: ClusteringStrategy
    redis_manager: RedisTaskManager

    def execute(self, command: ClusterizationRequestDTO) -> ClusteredGraphDTO | str:
        # Маппинг DTO -> Domain
        nodes = [
            GraphNode(
                node_id=n.id, 
                name=n.name, 
                index=n.index
            ) for n in command.graph.nodes
        ]
        links = [
            GraphLink(source=l.source, target=l.target) 
            for l in command.graph.links
        ]
        graph = Graph(nodes=nodes, links=links)

        # Асинхронный режим (через Redis)
        if command.async_mode:
            task_id = self.redis_manager.enqueue_clustering_task(command.model_dump())
            logger.info(f"Clustering task enqueued: {task_id}")
            return f"Task accepted: {task_id}"

        # Синхронный режим
        logger.info(f"Starting synchronous clustering for {len(nodes)} nodes...")
        
        # Попытка получить из кэша (опционально, если граф идентифицируем)
        # Но здесь граф передается целиком, кэшировать сложнее без хеша графа.
        # Опустим кэш для простоты при полной передаче графа.

        labels = self.clustering_strategy.clusterize(graph, n_clusters=command.n_clusters)
        graph.assign_clusters(labels)

        logger.info("Clustering completed.")

        # Маппинг Domain -> DTO
        response_nodes = [
            NodeDTO(
                id=n.node_id,
                name=n.name,
                index=n.index,
                cluster=n.cluster.value if n.cluster else None
            ) for n in graph.nodes
        ]
        
        response_links = [LinkDTO(source=l.source, target=l.target) for l in graph.links]

        return ClusteredGraphDTO(
            nodes=response_nodes,
            links=response_links,
            clusters_found=len(set(labels.values())) if labels else 0
        )

