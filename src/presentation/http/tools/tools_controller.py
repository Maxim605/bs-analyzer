from __future__ import annotations
from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.responses import Response
from urllib.parse import quote
import json
import os
import tempfile

from src.application.tools.commands.convert_data import ConvertDataHandler
from src.application.tools.dto.conversion_dto import D3GraphDTO


def create_tools_router(handler: ConvertDataHandler) -> APIRouter:
    """Создает роутер модуля Tools."""
    
    router = APIRouter(prefix="/tools", tags=["tools"])

    @router.post(
        "/d3-to-xlsx",
        responses={
            200: {
                "content": {"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {}},
                "description": "XLSX файл с матрицей смежности"
            }
        }
    )
    async def d3_json_to_xlsx(
        file: UploadFile = File(..., description="JSON файл с D3 графом")
    ):
        """
        POST /tools/d3-to-xlsx
        Конвертирует D3 JSON граф в XLSX матрицу смежности.
        
        Входной формат: JSON с полями nodes и links
        Выходной формат: XLSX файл с матрицей смежности
        """
        try:
            if not file.filename or not file.filename.endswith('.json'):
                raise HTTPException(
                    status_code=400,
                    detail="Файл должен быть в формате JSON (.json)"
                )
            
            content = await file.read()
            try:
                data = json.loads(content.decode('utf-8'))
            except json.JSONDecodeError as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Некорректный JSON формат: {str(e)}"
                )
            
            if 'nodes' not in data or 'links' not in data:
                raise HTTPException(
                    status_code=400,
                    detail="JSON должен содержать поля 'nodes' и 'links'"
                )
            
            graph = D3GraphDTO(**data)
            xlsx_bytes = handler.d3_json_to_xlsx(graph)
            
            output_filename = file.filename.replace('.json', '.xlsx')
            # RFC 5987: используем filename* для Unicode имен
            encoded_filename = quote(output_filename, safe='')
            
            return Response(
                content=xlsx_bytes,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={
                    "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
                }
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.post(
        "/xlsx-to-d3",
        responses={
            200: {
                "content": {"application/json": {}},
                "description": "JSON файл с D3 графом"
            }
        }
    )
    async def xlsx_to_d3_json(
        file: UploadFile = File(..., description="XLSX файл с матрицей смежности")
    ):
        """
        POST /tools/xlsx-to-d3
        Конвертирует XLSX матрицу смежности в D3 JSON граф.
        
        Входной формат: XLSX файл с матрицей смежности
        Выходной формат: JSON с полями nodes и links
        """
        try:
            if not file.filename or not file.filename.endswith('.xlsx'):
                raise HTTPException(
                    status_code=400,
                    detail="Файл должен быть в формате XLSX (.xlsx)"
                )
            
            content = await file.read()
            graph = handler.xlsx_to_d3_json(content)
            
            output_filename = file.filename.replace('.xlsx', '.json')
            result_json = graph.model_dump_json(indent=2)
            encoded_filename = quote(output_filename, safe='')
            
            return Response(
                content=result_json,
                media_type="application/json",
                headers={
                    "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
                }
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.post(
        "/npy-to-xlsx",
        responses={
            200: {
                "content": {"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {}},
                "description": "XLSX файл с матрицей"
            }
        }
    )
    async def npy_to_xlsx(
        file: UploadFile = File(..., description="NPY файл с numpy массивом")
    ):
        """
        POST /tools/npy-to-xlsx
        Конвертирует NPY файл в XLSX.
        
        Входной формат: NPY файл с numpy массивом
        Выходной формат: XLSX файл с матрицей
        """
        try:
            if not file.filename or not file.filename.endswith('.npy'):
                raise HTTPException(
                    status_code=400,
                    detail="Файл должен быть в формате NPY (.npy)"
                )
            
            content = await file.read()
            xlsx_bytes = handler.npy_to_xlsx(content)
            
            output_filename = file.filename.replace('.npy', '.xlsx')
            encoded_filename = quote(output_filename, safe='')
            
            return Response(
                content=xlsx_bytes,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={
                    "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
                }
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.post(
        "/xlsx-to-npy",
        responses={
            200: {
                "content": {"application/octet-stream": {}},
                "description": "NPY файл с numpy массивом"
            }
        }
    )
    async def xlsx_to_npy(
        file: UploadFile = File(..., description="XLSX файл с матрицей")
    ):
        """
        POST /tools/xlsx-to-npy
        Конвертирует XLSX файл в NPY.
        
        Входной формат: XLSX файл с матрицей
        Выходной формат: NPY файл с numpy массивом
        """
        try:
            if not file.filename or not file.filename.endswith('.xlsx'):
                raise HTTPException(
                    status_code=400,
                    detail="Файл должен быть в формате XLSX (.xlsx)"
                )
            
            content = await file.read()
            npy_bytes = handler.xlsx_to_npy(content)
            
            output_filename = file.filename.replace('.xlsx', '.npy')
            encoded_filename = quote(output_filename, safe='')
            
            return Response(
                content=npy_bytes,
                media_type="application/octet-stream",
                headers={
                    "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
                }
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    return router

