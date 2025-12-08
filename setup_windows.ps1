# Скрипт настройки для Windows
# Настройка переменных окружения и лимитов памяти для Big Sister Analyzer

Write-Host "=== Настройка Big Sister Analyzer для Windows ===" -ForegroundColor Green

# 1. Настройка переменных окружения для потоков
Write-Host "`n1. Настройка переменных окружения для потоков..." -ForegroundColor Yellow
$env:OMP_NUM_THREADS = "8"
$env:MKL_NUM_THREADS = "8"
$env:NUMEXPR_NUM_THREADS = "8"
$env:OPENBLAS_NUM_THREADS = "8"
$env:VECLIB_MAXIMUM_THREADS = "8"

Write-Host "   OMP_NUM_THREADS = $env:OMP_NUM_THREADS" -ForegroundColor Cyan
Write-Host "   MKL_NUM_THREADS = $env:MKL_NUM_THREADS" -ForegroundColor Cyan

# 2. Проверка доступной памяти
Write-Host "`n2. Проверка доступной памяти..." -ForegroundColor Yellow
$totalMemory = (Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB
$availableMemory = (Get-Counter '\Memory\Available MBytes').CounterSamples.CookedValue / 1024

Write-Host "   Всего памяти: $([math]::Round($totalMemory, 2)) GB" -ForegroundColor Cyan
Write-Host "   Доступно памяти: $([math]::Round($availableMemory, 2)) GB" -ForegroundColor Cyan

if ($totalMemory -lt 40) {
    Write-Host "   ВНИМАНИЕ: Рекомендуется минимум 40 GB ОЗУ!" -ForegroundColor Red
    Write-Host "   Текущая система имеет только $([math]::Round($totalMemory, 2)) GB" -ForegroundColor Red
} else {
    Write-Host "   ✓ Достаточно памяти для работы" -ForegroundColor Green
}

# 3. Проверка CPU
Write-Host "`n3. Проверка CPU..." -ForegroundColor Yellow
$cpuCores = (Get-CimInstance Win32_ComputerSystem).NumberOfLogicalProcessors
Write-Host "   Логических ядер CPU: $cpuCores" -ForegroundColor Cyan

if ($cpuCores -lt 8) {
    Write-Host "   ВНИМАНИЕ: Рекомендуется минимум 8 ядер!" -ForegroundColor Yellow
    Write-Host "   Текущая система имеет $cpuCores ядер" -ForegroundColor Yellow
} else {
    Write-Host "   ✓ Достаточно ядер CPU" -ForegroundColor Green
}

# 4. Настройка приоритета процесса (требует прав администратора)
Write-Host "`n4. Настройка приоритета процесса..." -ForegroundColor Yellow
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if ($isAdmin) {
    Write-Host "   ✓ Запущено с правами администратора" -ForegroundColor Green
    Write-Host "   Приоритет процесса будет установлен автоматически при запуске" -ForegroundColor Cyan
} else {
    Write-Host "   ⚠ Запущено без прав администратора" -ForegroundColor Yellow
    Write-Host "   Для оптимальной производительности запустите PowerShell от имени администратора" -ForegroundColor Yellow
}

# 5. Создание постоянных переменных окружения (опционально)
Write-Host "`n5. Настройка постоянных переменных окружения..." -ForegroundColor Yellow
$setPermanent = Read-Host "   Установить переменные окружения постоянно? (Y/N)"

if ($setPermanent -eq "Y" -or $setPermanent -eq "y") {
    if ($isAdmin) {
        [System.Environment]::SetEnvironmentVariable("OMP_NUM_THREADS", "8", "Machine")
        [System.Environment]::SetEnvironmentVariable("MKL_NUM_THREADS", "8", "Machine")
        [System.Environment]::SetEnvironmentVariable("NUMEXPR_NUM_THREADS", "8", "Machine")
        [System.Environment]::SetEnvironmentVariable("OPENBLAS_NUM_THREADS", "8", "Machine")
        Write-Host "   ✓ Переменные окружения установлены постоянно" -ForegroundColor Green
        Write-Host "   Перезагрузите PowerShell для применения изменений" -ForegroundColor Yellow
    } else {
        [System.Environment]::SetEnvironmentVariable("OMP_NUM_THREADS", "8", "User")
        [System.Environment]::SetEnvironmentVariable("MKL_NUM_THREADS", "8", "User")
        [System.Environment]::SetEnvironmentVariable("NUMEXPR_NUM_THREADS", "8", "User")
        [System.Environment]::SetEnvironmentVariable("OPENBLAS_NUM_THREADS", "8", "User")
        Write-Host "   ✓ Переменные окружения установлены для текущего пользователя" -ForegroundColor Green
        Write-Host "   Перезагрузите PowerShell для применения изменений" -ForegroundColor Yellow
    }
} else {
    Write-Host "   Переменные окружения установлены только для текущей сессии" -ForegroundColor Cyan
}

# 6. Информация о запуске
Write-Host "`n=== Готово к запуску ===" -ForegroundColor Green
Write-Host "`nДля запуска приложения выполните:" -ForegroundColor Yellow
Write-Host "   uvicorn src.main:app --reload" -ForegroundColor Cyan
Write-Host "`nИли используйте скрипт start.ps1" -ForegroundColor Yellow

Write-Host "`nДля мониторинга ресурсов используйте:" -ForegroundColor Yellow
Write-Host "   Get-Process python | Select-Object ProcessName, @{Name='Memory(GB)';Expression={[math]::Round(`$_.WorkingSet64/1GB, 2)}}" -ForegroundColor Cyan

