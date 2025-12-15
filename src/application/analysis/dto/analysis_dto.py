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

class OptimalClusterRequestDTO(AnalysisRequestDTO):
    min_k: int = Field(default=2, ge=2)
    max_k: int = Field(default=10, ge=2)

class EpochStatsDTO(BaseModel):
    k: int
    modularity: float
    stats: Dict[str, Any]

class OptimalClusterResponseDTO(BaseModel):
    optimal_k: int
    best_stats: Dict[str, Any]
    clustered_graph: Any # ClusteredGraphDTO нельзя импортировать из-за цикла, используем Dict или GraphSourceDTO с кластерами
    epoch_stats: List[EpochStatsDTO]

class LibraryMetricDTO(BaseModel):
    k: int
    silhouette_score: float
    calinski_harabasz_score: float
    davies_bouldin_score: float

class LibraryOptimalClusterResponseDTO(BaseModel):
    optimal_k: int
    method: str  # "silhouette", "calinski_harabasz", "davies_bouldin"
    optimal_score: float
    clustered_graph: Any
    metrics: List[LibraryMetricDTO]

