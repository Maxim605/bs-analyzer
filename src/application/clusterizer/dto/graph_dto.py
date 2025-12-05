from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List, Optional

class NodeDTO(BaseModel):
    id: str
    name: str
    index: Optional[int] = None
    cluster: Optional[int] = None

class LinkDTO(BaseModel):
    source: str
    target: str

class GraphSourceDTO(BaseModel):
    nodes: List[NodeDTO]
    links: List[LinkDTO]

class ClusterizationRequestDTO(BaseModel):
    graph: GraphSourceDTO
    n_clusters: int = Field(default=5, ge=2)
    async_mode: bool = False

class ClusteredGraphDTO(BaseModel):
    nodes: List[NodeDTO]
    links: List[LinkDTO]
    clusters_found: int

