from __future__ import annotations
from pydantic import BaseModel
from typing import List, Optional, Any


class D3NodeDTO(BaseModel):
    """DTO для узла D3 графа."""
    id: str
    name: Optional[str] = None
    index: Optional[int] = None
    cluster: Optional[int] = None
    
    class Config:
        extra = "allow"


class D3LinkDTO(BaseModel):
    """DTO для связи D3 графа."""
    source: str
    target: str
    weight: Optional[float] = None
    
    class Config:
        extra = "allow"


class D3GraphDTO(BaseModel):
    """DTO для D3 графа."""
    nodes: List[D3NodeDTO]
    links: List[D3LinkDTO]


class ConversionResponseDTO(BaseModel):
    """DTO для ответа конвертации."""
    success: bool
    message: str
    data: Optional[Any] = None

