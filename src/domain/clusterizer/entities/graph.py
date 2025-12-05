from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any
from src.domain.clusterizer.entities.graph_node import GraphNode

@dataclass
class GraphLink:
    source: str
    target: str

@dataclass
class Graph:
    """
    Агрегат Графа.
    Содержит узлы и связи.
    """
    nodes: List[GraphNode]
    links: List[GraphLink]

    def get_node_by_id(self, node_id: str) -> GraphNode | None:
        for node in self.nodes:
            if node.node_id == node_id:
                return node
        return None

    def assign_clusters(self, labels: Dict[str, int]) -> None:
        """Присваивает кластеры узлам на основе словаря {node_id: cluster_id}."""
        for node in self.nodes:
            if node.node_id in labels:
                node.set_cluster(labels[node.node_id])

    def to_adjacency_matrix_data(self) -> tuple[list[str], list[tuple[str, str]]]:
        """
        Подготавливает данные для построения матрицы смежности.
        Возвращает список ID узлов и список кортежей связей.
        """
        node_ids = [n.node_id for n in self.nodes]
        edges = [(l.source, l.target) for l in self.links]
        return node_ids, edges

