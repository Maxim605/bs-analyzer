# Настройка Big Sister Analyzer на Windows

## Быстрый старт

### Вариант 1: Автоматическая настройка (рекомендуется)

1. Откройте PowerShell в директории проекта
2. Запустите скрипт настройки:
   ```powershell
   .\setup_windows.ps1
   ```
3. Запустите приложение:
   ```powershell
   .\start.ps1
   ```

### Вариант 2: Ручная настройка

#### Шаг 1: Настройка переменных окружения

Откройте PowerShell и выполните:

```powershell
# Для текущей сессии
$env:OMP_NUM_THREADS = "8"
$env:MKL_NUM_THREADS = "8"
$env:NUMEXPR_NUM_THREADS = "8"
$env:OPENBLAS_NUM_THREADS = "8"
```

#### Шаг 2: Установка постоянных переменных окружения

**Через PowerShell (требует прав администратора):**

```powershell
# Запустите PowerShell от имени администратора
[System.Environment]::SetEnvironmentVariable("OMP_NUM_THREADS", "8", "Machine")
[System.Environment]::SetEnvironmentVariable("MKL_NUM_THREADS", "8", "Machine")
[System.Environment]::SetEnvironmentVariable("NUMEXPR_NUM_THREADS", "8", "Machine")
[System.Environment]::SetEnvironmentVariable("OPENBLAS_NUM_THREADS", "8", "Machine")
```

**Через графический интерфейс:**

1. Нажмите `Win + R`, введите `sysdm.cpl` и нажмите Enter
2. Перейдите на вкладку "Дополнительно"
3. Нажмите "Переменные среды"
4. В разделе "Системные переменные" нажмите "Создать"
5. Добавьте переменные:
   - `OMP_NUM_THREADS` = `8`
   - `MKL_NUM_THREADS` = `8`
   - `NUMEXPR_NUM_THREADS` = `8`
   - `OPENBLAS_NUM_THREADS` = `8`
6. Перезагрузите компьютер

#### Шаг 3: Настройка памяти

Windows автоматически управляет памятью, но вы можете оптимизировать:

**1. Настройка виртуальной памяти (файл подкачки):**

1. Нажмите `Win + R`, введите `sysdm.cpl` и нажмите Enter
2. Перейдите на вкладку "Дополнительно"
3. В разделе "Быстродействие" нажмите "Параметры"
4. Перейдите на вкладку "Дополнительно"
5. В разделе "Виртуальная память" нажмите "Изменить"
6. Снимите галочку "Автоматически выбирать объем файла подкачки"
7. Выберите системный диск
8. Установите "Указать размер":
   - Исходный размер: `40960` МБ (40 ГБ)
   - Максимальный размер: `40960` МБ (40 ГБ)
9. Нажмите "Задать" и "ОК"
10. Перезагрузите компьютер

**2. Настройка приоритета процесса:**

При запуске приложения через PowerShell с правами администратора:

```powershell
# Запуск с высоким приоритетом
Start-Process python -ArgumentList "-m uvicorn src.main:app --reload" -Priority High
```

Или вручную через Диспетчер задач:
1. Запустите приложение
2. Откройте Диспетчер задач (`Ctrl + Shift + Esc`)
3. Перейдите на вкладку "Подробности"
4. Найдите процесс `python.exe` или `uvicorn.exe`
5. Правый клик → "Задать приоритет" → "Высокий"

**3. Настройка соответствия процессоров:**

1. В Диспетчере задач найдите процесс Python
2. Правый клик → "Задать соответствие"
3. Выберите "Все процессоры" или конкретные ядра
4. Нажмите "ОК"

#### Шаг 4: Запуск приложения

```powershell
uvicorn src.main:app --reload
```

## Проверка настроек

### Проверка переменных окружения

```powershell
# Проверка текущих значений
echo $env:OMP_NUM_THREADS
echo $env:MKL_NUM_THREADS

# Или через системные переменные
[System.Environment]::GetEnvironmentVariable("OMP_NUM_THREADS", "Machine")
```

### Проверка доступной памяти

```powershell
# Общая память системы
(Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB

# Доступная память
(Get-Counter '\Memory\Available MBytes').CounterSamples.CookedValue / 1024

# Память процесса Python
Get-Process python -ErrorAction SilentlyContinue | 
    Select-Object ProcessName, @{Name="Memory(GB)";Expression={[math]::Round($_.WorkingSet64/1GB, 2)}}
```

### Проверка использования CPU

```powershell
# Количество логических ядер
(Get-CimInstance Win32_ComputerSystem).NumberOfLogicalProcessors

# Использование CPU процессом
Get-Process python -ErrorAction SilentlyContinue | Select-Object ProcessName, CPU
```

## Мониторинг производительности

### Мониторинг в реальном времени

```powershell
# Мониторинг памяти процесса
while ($true) {
    $proc = Get-Process python -ErrorAction SilentlyContinue
    if ($proc) {
        $memoryGB = [math]::Round($proc.WorkingSet64 / 1GB, 2)
        $cpu = $proc.CPU
        Write-Host "Memory: $memoryGB GB | CPU: $cpu" -ForegroundColor Cyan
    }
    Start-Sleep -Seconds 2
}
```

### Использование Диспетчера задач

1. Откройте Диспетчер задач (`Ctrl + Shift + Esc`)
2. Перейдите на вкладку "Производительность"
3. Выберите "Память" для мониторинга использования ОЗУ
4. Выберите "ЦП" для мониторинга использования процессора

## Оптимизация для продакшена

### Запуск как служба Windows

Создайте файл `big-sister-analyzer-service.ps1`:

```powershell
# Создание службы Windows (требует прав администратора)
$serviceName = "BigSisterAnalyzer"
$serviceDisplayName = "Big Sister Analyzer API"
$serviceDescription = "Big Sister Analyzer Graph Clustering Service"
$pythonPath = (Get-Command python).Source
$scriptPath = Join-Path $PSScriptRoot "src\main.py"
$workingDirectory = $PSScriptRoot

# Создание службы через NSSM (Non-Sucking Service Manager)
# Скачайте NSSM с https://nssm.cc/download
# nssm install $serviceName "$pythonPath" "-m uvicorn src.main:app --host 0.0.0.0 --port 8000"
# nssm set $serviceName AppDirectory $workingDirectory
# nssm set $serviceName AppEnvironmentExtra OMP_NUM_THREADS=8 MKL_NUM_THREADS=8
# nssm set $serviceName Description $serviceDescription
# nssm set $serviceName DisplayName $serviceDisplayName
# nssm start $serviceName
```

### Использование Windows Task Scheduler

1. Откройте Планировщик заданий (`Win + R` → `taskschd.msc`)
2. Создайте новое задание
3. Настройте:
   - Триггер: При запуске системы
   - Действие: Запуск программы
   - Программа: `python`
   - Аргументы: `-m uvicorn src.main:app --host 0.0.0.0 --port 8000`
   - Рабочая папка: путь к проекту
   - Параметры: Запускать с наивысшими правами

## Устранение проблем

### Проблема: "MemoryError" или нехватка памяти

**Решение:**
1. Увеличьте файл подкачки (см. Шаг 3 выше)
2. Закройте другие приложения
3. Уменьшите размер обрабатываемых графов
4. Используйте async режим для длительных операций

### Проблема: Низкая производительность

**Решение:**
1. Проверьте, что переменные окружения установлены:
   ```powershell
   echo $env:OMP_NUM_THREADS
   ```
2. Установите высокий приоритет процесса
3. Убедитесь, что используется достаточно памяти
4. Проверьте, что все ядра CPU доступны

### Проблема: Переменные окружения не применяются

**Решение:**
1. Перезагрузите PowerShell после установки переменных
2. Проверьте, что переменные установлены для правильного уровня (User/Machine)
3. Перезагрузите компьютер после установки системных переменных

## Рекомендации

1. **Для разработки:**
   - Используйте `start.ps1` для быстрого запуска
   - Мониторьте использование ресурсов через Диспетчер задач

2. **Для продакшена:**
   - Установите постоянные переменные окружения
   - Настройте службу Windows или Task Scheduler
   - Используйте мониторинг производительности

3. **Для больших графов:**
   - Убедитесь, что доступно минимум 40 ГБ ОЗУ
   - Используйте SSD для лучшей производительности
   - Рассмотрите использование async режима

