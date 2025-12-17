from __future__ import annotations

import logging
import os
import sys
from datetime import datetime
from fastapi import FastAPI

from src.infrastructure.config import config
from src.presentation.http.example.example_module import build_example_router
from src.presentation.http.clusterizer.clusterizer_module import build_clusterizer_module
from src.presentation.http.analysis.analysis_module import build_analysis_module
from src.presentation.http.users.users_module import build_users_module

# Оптимизация для максимального использования ресурсов CPU
# Настройка переменных окружения для numpy/scipy/sklearn
# По умолчанию: 8 потоков, 40 ГБ ОЗУ
DEFAULT_THREADS = 8
DEFAULT_MEMORY_GB = 40

os.environ['OMP_NUM_THREADS'] = str(DEFAULT_THREADS)  # OpenMP threads для numpy/scipy
os.environ['MKL_NUM_THREADS'] = str(DEFAULT_THREADS)  # Intel MKL threads
os.environ['NUMEXPR_NUM_THREADS'] = str(DEFAULT_THREADS)  # NumExpr threads
os.environ['OPENBLAS_NUM_THREADS'] = str(DEFAULT_THREADS)  # OpenBLAS threads
os.environ['VECLIB_MAXIMUM_THREADS'] = str(DEFAULT_THREADS)  # macOS Accelerate framework

# Настройка памяти (для больших графов)
# Python не имеет прямого способа резервирования памяти, но можно настроить лимиты
# Для Windows: используйте системные настройки или запускайте с увеличенным лимитом
# Для Linux: можно использовать ulimit или systemd limits

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

# Логирование настроек параллелизма
cpu_count = os.cpu_count() or 1
logging.info(f"CPU cores detected: {cpu_count}")
logging.info(f"Parallel processing configured: {DEFAULT_THREADS} threads")
logging.info(f"Memory allocation: {DEFAULT_MEMORY_GB} GB (recommended)")
logging.info(f"OMP_NUM_THREADS={os.environ.get('OMP_NUM_THREADS')}")

app = FastAPI(title="Документация API", version="0.1.0")

# Подключение роутеров
app.include_router(build_example_router())
app.include_router(build_clusterizer_module())
app.include_router(build_analysis_module())
app.include_router(build_users_module())


@app.get("/health")
def health() -> dict:
    """GET /health - Проверка состояния сервиса"""
    return {
            "name": "big-sister-analyzer",
            "status": "ok",
            "version": "0.1.0"
        }


