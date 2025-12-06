from __future__ import annotations
import networkx as nx
import numpy as np
from typing import List, Dict, Any

from src.domain.clusterizer.entities.graph import Graph
from src.domain.analysis.services.graph_analysis_service import GraphAnalysisService

class NetworkXGraphAnalysisService(GraphAnalysisService):
    """
    Реализация сервиса анализа графа через NetworkX и NumPy.
    """

    def _to_nx_graph(self, graph: Graph) -> nx.Graph:
        node_ids, edges = graph.to_adjacency_matrix_data()
        nx_graph = nx.Graph()
        nx_graph.add_nodes_from(node_ids)
        nx_graph.add_edges_from(edges)
        return nx_graph

    def get_adjacency_matrix(self, graph: Graph) -> List[List[int]]:
        nx_graph = self._to_nx_graph(graph)
        # to_numpy_array возвращает float, конвертируем в int
        adj_matrix = nx.to_numpy_array(nx_graph, dtype=int)
        return adj_matrix.tolist()

    def get_laplacian_matrix(self, graph: Graph) -> List[List[int]]:
        nx_graph = self._to_nx_graph(graph)
        lap_matrix = nx.laplacian_matrix(nx_graph).toarray().astype(int)
        return lap_matrix.tolist()

    def get_eigenvalues(self, graph: Graph, k: int = 6) -> List[float]:
        nx_graph = self._to_nx_graph(graph)
        # Используем лапласиан для собственных чисел
        L = nx.laplacian_matrix(nx_graph).astype(float)
        # Получаем собственные числа. k=min(len(nodes)-2, k) чтобы не выйти за границы
        import scipy.sparse.linalg
        num_nodes = nx_graph.number_of_nodes()
        if num_nodes <= 2:
             return [0.0] * num_nodes
        
        k_adjusted = min(k, num_nodes - 2) # eigsh требует k < N-1
        if k_adjusted <= 0:
            # Для очень малых графов используем numpy
            vals = np.linalg.eigvalsh(L.toarray())
            return sorted(vals.tolist())[:k]

        vals = scipy.sparse.linalg.eigsh(L, k=k_adjusted, which='SM', return_eigenvectors=False)
        return sorted(vals.tolist())

    def get_chromatic_number(self, graph: Graph) -> int:
        nx_graph = self._to_nx_graph(graph)
        # greedy_color возвращает словарь раскраски, нам нужно число цветов
        coloring = nx.coloring.greedy_color(nx_graph, strategy='largest_first')
        if not coloring:
            return 0
        return max(coloring.values()) + 1

    def get_basic_stats(self, graph: Graph) -> Dict[str, Any]:
        nx_graph = self._to_nx_graph(graph)
        num_nodes = nx_graph.number_of_nodes()
        num_edges = nx_graph.number_of_edges()
        
        stats = {
            "nodes_count": num_nodes,
            "edges_count": num_edges,
            "density": nx.density(nx_graph),
            "average_clustering": 0.0,
            "is_connected": nx.is_connected(nx_graph),
            "number_connected_components": nx.number_connected_components(nx_graph),
        }
        
        # Вычисление более тяжелых метрик только если граф не слишком большой
        # Или для демо целей считаем всё
        stats["average_clustering"] = nx.average_clustering(nx_graph)
        
        if stats["is_connected"]:
            stats["diameter"] = nx.diameter(nx_graph)
            stats["average_shortest_path_length"] = nx.average_shortest_path_length(nx_graph)
        else:
            # Для несвязных графов можно посчитать для самой большой компоненты
            largest_cc = max(nx.connected_components(nx_graph), key=len)
            subgraph = nx_graph.subgraph(largest_cc)
            stats["diameter_largest_component"] = nx.diameter(subgraph)
            
        return stats

