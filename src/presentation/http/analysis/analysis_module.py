from __future__ import annotations
from fastapi import APIRouter

from src.infrastructure.config import config
from src.infrastructure.clusterizer.redis.redis_manager import RedisTaskManager
from src.infrastructure.analysis.services.networkx_analysis import NetworkXGraphAnalysisService
from src.infrastructure.clusterizer.services.sklearn_clustering import SklearnSpectralClusteringStrategy
from src.application.analysis.queries.analyze_graph import AnalyzeGraphHandler
from src.presentation.http.analysis.analysis_controller import create_analysis_router

def build_analysis_module() -> APIRouter:
    """
    Сборка модуля Analysis (Composition Root).
    """
    # 1. Infrastructure
    redis_manager = RedisTaskManager(host=config.REDIS_HOST, port=config.REDIS_PORT, db=config.REDIS_DB)
    analysis_service = NetworkXGraphAnalysisService()
    clustering_strategy = SklearnSpectralClusteringStrategy()

    # 2. Application
    analysis_handler = AnalyzeGraphHandler(
        analysis_service=analysis_service,
        redis_manager=redis_manager,
        clustering_strategy=clustering_strategy
    )

    # 3. Presentation
    router = create_analysis_router(analysis_handler)
    
    return router

