# Конфигурация памяти и потоков

## Настройки по умолчанию

- **Потоки**: 8
- **ОЗУ**: 40 ГБ (рекомендуется)

## Настройка памяти

### Windows

#### PowerShell (для текущей сессии)
```powershell
# Увеличить лимит памяти для процесса (требует прав администратора)
$env:PYTHONHASHSEED="0"
# Запуск с увеличенным лимитом памяти
uvicorn src.main:app --reload
```

#### Через системные настройки
1. Откройте "Диспетчер задач" → "Подробности"
2. Найдите процесс Python
3. Правый клик → "Установить приоритет" → "Высокий"
4. Правый клик → "Задать соответствие" → выберите все ядра CPU

#### Через групповую политику (для сервера)
```powershell
# Установить лимит памяти для процесса (в байтах, 40 ГБ = 42949672960 байт)
# Это делается через системные настройки Windows
```

### Linux

#### Установка лимитов через ulimit
```bash
# Увеличить лимит памяти (40 ГБ в килобайтах = 41943040)
ulimit -v 41943040

# Увеличить лимит виртуальной памяти
ulimit -m 41943040

# Запуск приложения
uvicorn src.main:app --reload
```

#### Через systemd (для сервиса)
Создайте файл `/etc/systemd/system/big-sister-analyzer.service`:

```ini
[Unit]
Description=Big Sister Analyzer
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/big-sister-analyzer
Environment="PYTHONUNBUFFERED=1"
Environment="OMP_NUM_THREADS=8"
Environment="MKL_NUM_THREADS=8"
LimitAS=40G
LimitRSS=40G
ExecStart=/usr/bin/uvicorn src.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Затем:
```bash
sudo systemctl daemon-reload
sudo systemctl enable big-sister-analyzer
sudo systemctl start big-sister-analyzer
```

### Docker

#### docker-compose.yml
```yaml
version: '3.8'
services:
  app:
    build: .
    deploy:
      resources:
        limits:
          cpus: '8'
          memory: 40G
        reservations:
          memory: 40G
    environment:
      - OMP_NUM_THREADS=8
      - MKL_NUM_THREADS=8
```

#### Docker run
```bash
docker run --cpus="8" --memory="40g" your-image
```

## Изменение настроек потоков

### Через переменные окружения

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

### Через код

Измените константы в `src/main.py`:

```python
DEFAULT_THREADS = 8  # Измените на нужное значение
DEFAULT_MEMORY_GB = 40  # Измените на нужное значение
```

## Проверка использования ресурсов

### Windows PowerShell
```powershell
# Мониторинг памяти процесса
Get-Process python | Select-Object ProcessName, @{Name="Memory(GB)";Expression={[math]::Round($_.WorkingSet64/1GB, 2)}}

# Мониторинг CPU
Get-Process python | Select-Object ProcessName, CPU
```

### Linux
```bash
# Мониторинг памяти
ps aux | grep uvicorn | awk '{print $2, $6/1024/1024 " GB"}'

# Детальный мониторинг
top -p $(pgrep -f uvicorn)
```

## Рекомендации

1. **Для больших графов (>100K узлов):**
   - Убедитесь, что доступно минимум 40 ГБ ОЗУ
   - Используйте async режим для длительных операций
   - Рассмотрите использование SSD для кэширования

2. **Для продакшена:**
   - Настройте мониторинг памяти
   - Используйте swap файл (если необходимо)
   - Настройте автоматический перезапуск при превышении лимитов

3. **Оптимизация:**
   - Используйте разреженные матрицы (уже реализовано)
   - Кэшируйте результаты кластеризации
   - Используйте батчинг для обработки нескольких графов

## Устранение проблем

### Ошибка "MemoryError"
- Увеличьте доступную память
- Уменьшите размер графа (разбейте на части)
- Используйте более эффективные структуры данных

### Низкая производительность
- Проверьте, что используются все 8 потоков
- Убедитесь, что нет конкуренции за ресурсы
- Проверьте использование CPU через мониторинг

