from abc import ABC, abstractmethod
from typing import List, Tuple, Any, Dict
from src.domain.clusterizer.entities.graph import Graph

class GraphAnalysisService(ABC):
    """Интерфейс сервиса анализа графа (Domain Service Interface)."""

    @abstractmethod
    def get_adjacency_matrix(self, graph: Graph) -> List[List[int]]:
        """Возвращает матрицу смежности."""
        pass

    @abstractmethod
    def get_laplacian_matrix(self, graph: Graph) -> List[List[int]]:
        """Возвращает матрицу Лапласа."""
        pass

    @abstractmethod
    def get_eigenvalues(self, graph: Graph, k: int = 6) -> List[float]:
        """Возвращает k первых собственных чисел матрицы Лапласа."""
        pass

    @abstractmethod
    def get_chromatic_number(self, graph: Graph) -> int:
        """Возвращает хроматическое число графа."""
        pass

    @abstractmethod
    def get_basic_stats(self, graph: Graph) -> Dict[str, Any]:
        """Возвращает основные характеристики: плотность, диаметр, среднюю степень и т.д."""
        pass

