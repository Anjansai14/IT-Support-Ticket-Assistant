#!/usr/bin/env bash
# ========================================================
# IT Support Ticket Assistant - POSIX Launcher (macOS / Linux / WSL)
# ========================================================

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

# 1. Create venv if not present
if [ ! -f ".venv/bin/python" ]; then
    echo "[INFO] Creating virtual environment (.venv)..."
    python3 -m venv .venv
    .venv/bin/pip install --upgrade pip
    .venv/bin/pip install -r backend/requirements.txt
fi

# 2. Copy .env if not present
if [ ! -f "backend/.env" ] && [ -f "backend/.env.example" ]; then
    cp backend/.env.example backend/.env
    echo "[INFO] Initialized backend/.env from template."
fi

# 3. Launch universal runner
echo "[INFO] Starting IT Support Ticket Assistant on http://localhost:8000 ..."
.venv/bin/python run.py
