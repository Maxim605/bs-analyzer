from __future__ import annotations
from typing import Dict, Any, List
import numpy as np

from src.domain.tools.services.converter_interface import IDataConverter
from src.application.tools.dto.conversion_dto import D3GraphDTO


class ConvertDataHandler:
    """Хендлер для конвертации данных между форматами."""

    def __init__(self, converter: IDataConverter):
        self._converter = converter

    def d3_json_to_xlsx(self, graph: D3GraphDTO) -> bytes:
        """
        Конвертирует D3 JSON в XLSX матрицу смежности.
        
        Args:
            graph: D3 граф
            
        Returns:
            Байты XLSX файла
        """
        nodes = [node.model_dump() for node in graph.nodes]
        links = [link.model_dump() for link in graph.links]
        
        matrix, headers = self._converter.d3_json_to_adjacency_matrix(nodes, links)
        return self._converter.matrix_to_xlsx_bytes(matrix, headers)

    def xlsx_to_d3_json(self, xlsx_bytes: bytes) -> D3GraphDTO:
        """
        Конвертирует XLSX матрицу смежности в D3 JSON.
        
        Args:
            xlsx_bytes: Байты XLSX файла
            
        Returns:
            D3 граф
        """
        matrix, headers = self._converter.xlsx_bytes_to_matrix(xlsx_bytes)
        d3_data = self._converter.adjacency_matrix_to_d3_json(matrix, headers)
        return D3GraphDTO(**d3_data)

    def npy_to_xlsx(self, npy_bytes: bytes, headers: List[str] | None = None) -> bytes:
        """
        Конвертирует NPY в XLSX.
        
        Args:
            npy_bytes: Байты NPY файла
            headers: Опциональные заголовки
            
        Returns:
            Байты XLSX файла
        """
        matrix = self._converter.npy_to_matrix(npy_bytes)
        
        if headers is None:
            headers = [str(i) for i in range(matrix.shape[0])]
        
        return self._converter.matrix_to_xlsx_bytes(matrix, headers)

    def xlsx_to_npy(self, xlsx_bytes: bytes) -> bytes:
        """
        Конвертирует XLSX в NPY.
        
        Args:
            xlsx_bytes: Байты XLSX файла
            
        Returns:
            Байты NPY файла
        """
        matrix, _ = self._converter.xlsx_bytes_to_matrix(xlsx_bytes)
        return self._converter.matrix_to_npy_bytes(matrix)

