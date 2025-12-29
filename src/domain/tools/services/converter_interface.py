from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, Any, List
import numpy as np


class IDataConverter(ABC):
    """Интерфейс для конвертации данных между форматами."""

    @abstractmethod
    def d3_json_to_adjacency_matrix(
        self, 
        nodes: List[Dict[str, Any]], 
        links: List[Dict[str, Any]]
    ) -> tuple[np.ndarray, List[str]]:
        """
        Конвертирует D3 JSON граф в матрицу смежности.
        
        Args:
            nodes: Список узлов [{id, name, ...}]
            links: Список связей [{source, target}]
            
        Returns:
            Кортеж (матрица смежности NxN, список имен узлов)
        """
        pass

    @abstractmethod
    def adjacency_matrix_to_d3_json(
        self, 
        matrix: np.ndarray, 
        node_names: List[str]
    ) -> Dict[str, Any]:
        """
        Конвертирует матрицу смежности в D3 JSON формат.
        
        Args:
            matrix: Матрица смежности NxN
            node_names: Список имен узлов
            
        Returns:
            D3 JSON граф {nodes: [...], links: [...]}
        """
        pass

    @abstractmethod
    def matrix_to_xlsx_bytes(
        self, 
        matrix: np.ndarray, 
        headers: List[str]
    ) -> bytes:
        """
        Конвертирует матрицу в XLSX формат.
        
        Args:
            matrix: Матрица данных
            headers: Заголовки строк/столбцов
            
        Returns:
            Байты XLSX файла
        """
        pass

    @abstractmethod
    def xlsx_bytes_to_matrix(
        self, 
        xlsx_bytes: bytes
    ) -> tuple[np.ndarray, List[str]]:
        """
        Читает матрицу из XLSX файла.
        
        Args:
            xlsx_bytes: Байты XLSX файла
            
        Returns:
            Кортеж (матрица данных, заголовки)
        """
        pass

    @abstractmethod
    def npy_to_matrix(self, npy_bytes: bytes) -> np.ndarray:
        """
        Читает numpy массив из NPY файла.
        
        Args:
            npy_bytes: Байты NPY файла
            
        Returns:
            Numpy массив
        """
        pass

    @abstractmethod
    def matrix_to_npy_bytes(self, matrix: np.ndarray) -> bytes:
        """
        Конвертирует numpy массив в NPY формат.
        
        Args:
            matrix: Numpy массив
            
        Returns:
            Байты NPY файла
        """
        pass

