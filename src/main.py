from __future__ import annotations

from datetime import datetime
from fastapi import FastAPI

from src.presentation.http.example.example_module import build_example_router


app = FastAPI(title="Документация API", version="0.1.0")

# Подключение роутеров
app.include_router(build_example_router())


@app.get("/health")
def health() -> dict:
    """GET /health - Проверка состояния сервиса"""
    return {
            "name": "big-sister-analyzer",
            "status": "ok",
            "version": "0.1.0"
        }


