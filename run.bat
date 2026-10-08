@echo off
title IT Support Ticket Assistant
echo ========================================================
echo Starting IT Support Ticket Assistant Backend & Frontend...
echo ========================================================

cd /d "%~dp0"

REM 1. Check and auto-create virtual environment if missing
if not exist ".venv\Scripts\python.exe" (
    echo [.venv not found] Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Python is not found in your system PATH. Please install Python 3.10+ from python.org
        pause
        exit /b 1
    )
    echo Installing dependencies from backend\requirements.txt...
    ".venv\Scripts\python.exe" -m pip install --upgrade pip
    ".venv\Scripts\python.exe" -m pip install -r backend\requirements.txt
)

REM 2. Create .env if it doesn't exist
if not exist "backend\.env" (
    if exist "backend\.env.example" (
        copy "backend\.env.example" "backend\.env" >nul
        echo Initialized backend\.env configuration file.
    )
)

REM 3. Launch server using universal run.py
".venv\Scripts\python.exe" run.py

pause
