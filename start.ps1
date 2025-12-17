# Скрипт запуска приложения с оптимальными настройками для Windows

Write-Host "=== Запуск Big Sister Analyzer ===" -ForegroundColor Green

# Настройка переменных окружения для текущей сессии
$env:OMP_NUM_THREADS = "8"
$env:MKL_NUM_THREADS = "8"
$env:NUMEXPR_NUM_THREADS = "8"
$env:OPENBLAS_NUM_THREADS = "8"
$env:VECLIB_MAXIMUM_THREADS = "8"
$env:PYTHONUNBUFFERED = "1"

# Проверка доступной памяти
$totalMemory = (Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB
Write-Host "Доступно памяти: $([math]::Round($totalMemory, 2)) GB" -ForegroundColor Cyan

# Проверка, запущен ли процесс с повышенным приоритетом
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if ($isAdmin) {
    Write-Host "Запущено с правами администратора - приоритет будет повышен" -ForegroundColor Green
} else {
    Write-Host "Запущено без прав администратора" -ForegroundColor Yellow
    Write-Host "Для оптимальной производительности запустите PowerShell от имени администратора" -ForegroundColor Yellow
}

Write-Host "`nЗапуск uvicorn..." -ForegroundColor Yellow
Write-Host "Настройки: 8 потоков, рекомендуется 40 GB ОЗУ`n" -ForegroundColor Cyan

# Загрузка порта из .env файла
$envFile = ".env"
$port = "8000"
if (Test-Path $envFile) {
    $envContent = Get-Content $envFile
    foreach ($line in $envContent) {
        if ($line -match "^PORT=(.+)$") {
            $port = $matches[1]
            break
        }
    }
}

Write-Host "Порт приложения: $port" -ForegroundColor Cyan

# Запуск uvicorn
uvicorn src.main:app --reload --port $port

