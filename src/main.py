from __future__ import annotations

import logging
import sys
from datetime import datetime
from fastapi import FastAPI

from src.presentation.http.example.example_module import build_example_router
from src.presentation.http.clusterizer.clusterizer_module import build_clusterizer_module
from src.presentation.http.analysis.analysis_module import build_analysis_module

# Настройка логирования для вывода в консоль uvicorn
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Настройка уровня логирования для uvicorn
logging.getLogger("uvicorn").setLevel(logging.INFO)
logging.getLogger("uvicorn.access").setLevel(logging.INFO)

# Настройка уровня логирования для приложения
logging.getLogger("src").setLevel(logging.INFO)

app = FastAPI(title="Документация API", version="0.1.0")

# Подключение роутеров
app.include_router(build_example_router())
app.include_router(build_clusterizer_module())
app.include_router(build_analysis_module())


@app.get("/health")
def health() -> dict:
    """GET /health - Проверка состояния сервиса"""
    return {
            "name": "big-sister-analyzer",
            "status": "ok",
            "version": "0.1.0"
        }


