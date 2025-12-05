from __future__ import annotations
from fastapi import APIRouter

from src.infrastructure.clusterizer.services.sklearn_clustering import SklearnSpectralClusteringStrategy
from src.infrastructure.clusterizer.redis.redis_manager import RedisTaskManager
from src.application.clusterizer.commands.cluster_graph import ClusterGraphHandler
from src.presentation.http.clusterizer.clusterizer_controller import create_clusterizer_router

def build_clusterizer_module() -> APIRouter:
    """
    Сборка модуля Clusterizer (Composition Root).
    Инициализация зависимостей и инъекция.
    """
    # 1. Infrastructure
    # В продакшене параметры Redis стоило бы брать из конфига/env
    redis_manager = RedisTaskManager(host='localhost', port=6379) 
    clustering_strategy = SklearnSpectralClusteringStrategy()

    # 2. Application
    cluster_handler = ClusterGraphHandler(
        clustering_strategy=clustering_strategy,
        redis_manager=redis_manager
    )

    # 3. Presentation
    router = create_clusterizer_router(cluster_handler)
    
    return router

