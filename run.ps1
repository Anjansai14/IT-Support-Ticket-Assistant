Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "Starting IT Support Ticket Assistant Server..." -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Cyan

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = Join-Path $scriptDir "backend"
Set-Location $backendDir

$venvPython = Join-Path $scriptDir ".venv\Scripts\python.exe"

if (Test-Path $venvPython) {
    Write-Host "Using project virtual environment: $venvPython" -ForegroundColor DarkCyan
    & $venvPython -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
} else {
    Write-Host "Virtual environment not detected. Using default python..." -ForegroundColor Yellow
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
}
