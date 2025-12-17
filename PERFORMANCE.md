# Оптимизация производительности кластеризации

## Автоматическая оптимизация

Приложение автоматически настраивается для максимального использования ресурсов CPU при запуске.

### Что настроено автоматически:

1. **Переменные окружения для NumPy/SciPy/Sklearn:**
   - `OMP_NUM_THREADS` - OpenMP потоки для NumPy/SciPy
   - `MKL_NUM_THREADS` - Intel MKL потоки
   - `NUMEXPR_NUM_THREADS` - NumExpr потоки
   - `OPENBLAS_NUM_THREADS` - OpenBLAS потоки
   - `VECLIB_MAXIMUM_THREADS` - macOS Accelerate framework

2. **Scikit-learn SpectralClustering:**
   - `n_jobs=-1` - использует все доступные ядра CPU
   - `n_init='auto'` - автоматический выбор количества инициализаций

## Ручная настройка

### Запуск uvicorn с максимальными ресурсами

```bash
# Базовый запуск (автоматически использует все ядра)
uvicorn src.main:app --reload

# Для продакшена с большим количеством воркеров
uvicorn src.main:app --workers 4 --host 0.0.0.0 --port 8000

# С указанием количества потоков на воркер
uvicorn src.main:app --workers 4 --threads 2
```

### Переменные окружения для тонкой настройки

Вы можете переопределить настройки параллелизма через переменные окружения:

```bash
# Windows PowerShell
$env:OMP_NUM_THREADS="8"
$env:MKL_NUM_THREADS="8"
uvicorn src.main:app --reload

# Linux/Mac
export OMP_NUM_THREADS=8
export MKL_NUM_THREADS=8
uvicorn src.main:app --reload
```

### Рекомендации по настройке

1. **Для CPU-интенсивных задач:**
   - Используйте `--workers` равное количеству CPU ядер
   - Оставьте `n_jobs=-1` в SpectralClustering (по умолчанию)

2. **Для I/O-интенсивных задач:**
   - Увеличьте количество воркеров: `--workers 8`
   - Можно использовать больше воркеров, чем ядер CPU

3. **Для больших графов:**
   - Убедитесь, что достаточно RAM
   - Рассмотрите использование async режима для длительных операций

## Мониторинг производительности

При запуске приложения логируется информация о настройках:

```
INFO: CPU cores detected: 8
INFO: Parallel processing configured: OMP_NUM_THREADS=8
```

Во время выполнения кластеризации логируется прогресс:

```
INFO: Progress: 11.1% | Iteration 1/9 (k=2) | Modularity: 0.4523 | Iteration time: 1.23s | Total elapsed: 1.23s
```

## Проверка использования ресурсов

### Windows
```powershell
# Мониторинг CPU и памяти
Get-Process python | Select-Object CPU, WorkingSet
```

### Linux/Mac
```bash
# Мониторинг CPU и памяти
top -p $(pgrep -f uvicorn)
# или
htop -p $(pgrep -f uvicorn)
```

## Оптимизация для Docker

При запуске в Docker контейнере:

```dockerfile
# Укажите количество CPU ядер
docker run --cpus="4" your-image

# Или через docker-compose
services:
  app:
    deploy:
      resources:
        limits:
          cpus: '4'
```

## Известные ограничения

1. **GIL (Global Interpreter Lock) в Python:**
   - Некоторые операции могут не использовать все ядра эффективно
   - NumPy/SciPy обходят GIL через C-расширения

2. **Память:**
   - Большие графы требуют много RAM
   - Следите за использованием памяти при обработке больших графов

3. **Redis:**
   - Убедитесь, что Redis настроен для обработки нагрузки
   - Для продакшена настройте персистентность и репликацию

