from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
from src.domain.clusterizer.value_objects.cluster_id import ClusterId

@dataclass
class GraphNode:
    """Сущность узла графа (пользователя)."""
    node_id: str
    name: str
    cluster: Optional[ClusterId] = None
    _key: Optional[str] = None
    index: Optional[int] = None
    metadata: dict = field(default_factory=dict)

    def set_cluster(self, cluster_id: int) -> None:
        self.cluster = ClusterId(cluster_id)

