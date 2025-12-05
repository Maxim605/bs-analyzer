from abc import ABC, abstractmethod
from typing import Dict
from src.domain.clusterizer.entities.graph import Graph

class ClusteringStrategy(ABC):
    """Интерфейс стратегии кластеризации (Domain Service Interface)."""

    @abstractmethod
    def clusterize(self, graph: Graph, n_clusters: int = 2) -> Dict[str, int]:
        """
        Выполняет кластеризацию графа.
        Возвращает словарь {node_id: cluster_id}.
        """
        pass

