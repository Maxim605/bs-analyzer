from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from src.application.clusterizer.dto.graph_dto import GraphSourceDTO

class AnalysisRequestDTO(BaseModel):
    graph: GraphSourceDTO
    async_mode: bool = False

class AdjacencyMatrixDTO(BaseModel):
    matrix: List[List[int]]

class LaplacianMatrixDTO(BaseModel):
    matrix: List[List[int]]

class EigenvaluesDTO(BaseModel):
    values: List[float]

class ChromaticNumberDTO(BaseModel):
    chromatic_number: int

class GraphStatsDTO(BaseModel):
    stats: Dict[str, Any]

