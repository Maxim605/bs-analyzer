from __future__ import annotations
import networkx as nx
import numpy as np
from scipy import sparse
from sklearn.cluster import SpectralClustering
from typing import Dict

from src.domain.clusterizer.entities.graph import Graph
from src.domain.clusterizer.services.clustering_strategy import ClusteringStrategy

class SklearnSpectralClusteringStrategy(ClusteringStrategy):
    """
    Реализация спектральной кластеризации через Scikit-Learn.
    Оптимизирована для графов социальных сетей (разреженные матрицы).
    """

    def clusterize(self, graph: Graph, n_clusters: int = 5) -> Dict[str, int]:
        node_ids, edges = graph.to_adjacency_matrix_data()
        
        if not node_ids:
            return {}

        # Построение графа NetworkX для удобного получения матрицы смежности
        nx_graph = nx.Graph()
        nx_graph.add_nodes_from(node_ids)
        nx_graph.add_edges_from(edges)

        # Получение матрицы смежности (sparse matrix)
        adj_matrix = nx.to_scipy_sparse_array(nx_graph, nodelist=node_ids, format='csr')
        
        # Преобразование индексов к int32 для совместимости с scikit-learn
        # Scikit-learn требует int32 индексы в sparse матрицах (indices и indptr)
        # Данные оставляем как есть (обычно float64 или int)
        adj_matrix = sparse.csr_matrix(
            (adj_matrix.data, adj_matrix.indices.astype(np.int32), adj_matrix.indptr.astype(np.int32)),
            shape=adj_matrix.shape,
            dtype=adj_matrix.dtype
        )

        # Спектральная кластеризация
        # affinity='precomputed' - используем предвычисленную матрицу смежности
        sc = SpectralClustering(
            n_clusters=n_clusters, 
            affinity='precomputed', 
            assign_labels='kmeans',
            random_state=42,
            n_jobs=-1
        )
        
        labels = sc.fit_predict(adj_matrix)

        # Маппинг результатов обратно на ID узлов
        result = {}
        for i, node_id in enumerate(node_ids):
            result[node_id] = int(labels[i])
            
        return result

