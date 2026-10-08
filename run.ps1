Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "Starting IT Support Ticket Assistant Server..." -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Cyan

$rootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $rootDir

$venvPython = Join-Path $rootDir ".venv\Scripts\python.exe"

# 1. Check and create virtual environment if not present
if (-not (Test-Path $venvPython)) {
    Write-Host "[.venv not found] Creating virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Python is not found in your system PATH. Please install Python from python.org"
        exit 1
    }
    Write-Host "Installing dependencies from backend/requirements.txt..." -ForegroundColor DarkCyan
    & $venvPython -m pip install --upgrade pip
    & $venvPython -m pip install -r backend/requirements.txt
}

# 2. Check and copy .env
$envFile = Join-Path $rootDir "backend\.env"
$envExample = Join-Path $rootDir "backend\.env.example"
if (-not (Test-Path $envFile) -and (Test-Path $envExample)) {
    Copy-Item $envExample $envFile
    Write-Host "Initialized backend/.env file from template." -ForegroundColor DarkCyan
}

# 3. Start server using universal run.py
& $venvPython run.py
