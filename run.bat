@echo off
title IT Support Ticket Assistant
echo ========================================================
echo Starting IT Support Ticket Assistant Backend & Frontend...
echo ========================================================

cd /d "%~dp0backend"

if exist "..\.venv\Scripts\python.exe" (
    echo Using project virtual environment [.venv]...
    "..\.venv\Scripts\python.exe" -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
) else (
    echo [WARNING] .venv not found. Falling back to system python...
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
)

pause
