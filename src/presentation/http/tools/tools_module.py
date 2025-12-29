from __future__ import annotations
from fastapi import APIRouter

from src.infrastructure.tools.services.data_converter import DataConverterService
from src.application.tools.commands.convert_data import ConvertDataHandler
from src.presentation.http.tools.tools_controller import create_tools_router


def build_tools_module() -> APIRouter:
    """
    Сборка модуля Tools (Composition Root).
    """
    # 1. Infrastructure
    converter_service = DataConverterService()
    
    # 2. Application
    convert_handler = ConvertDataHandler(converter=converter_service)
    
    # 3. Presentation
    router = create_tools_router(convert_handler)
    
    return router

