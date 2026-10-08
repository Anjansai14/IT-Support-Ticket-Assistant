"""
Universal entry point for IT Support Ticket Assistant.
Compatible with all IDEs (VS Code, PyCharm, Cursor, Windsurf, Eclipse, Sublime, Spyder, etc.)
and all operating systems (Windows, macOS, Linux).
"""
import sys
import os
from pathlib import Path

# Safe UTF-8 reconfiguration for Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# 1. Ensure backend directory is in sys.path
ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# 2. Auto-initialize backend/.env if missing
env_file = BACKEND_DIR / ".env"
env_example = BACKEND_DIR / ".env.example"
if not env_file.exists() and env_example.exists():
    try:
        import shutil
        shutil.copy(env_example, env_file)
        print("[INFO] Initialized backend/.env from template.")
    except Exception as e:
        print(f"[WARN] Could not copy .env template: {e}")

if __name__ == "__main__":
    try:
        import uvicorn
    except ImportError:
        print("\n" + "=" * 65)
        print("[ERROR] uvicorn is not installed in the active Python environment.")
        print("Please install requirements using:")
        print("    pip install -r backend/requirements.txt")
        print("=" * 65 + "\n")
        sys.exit(1)

    print("\n" + "=" * 65)
    print(" IT Support Ticket Assistant - Server Starting")
    print("=" * 65)
    print(" [Web Dashboard]   http://localhost:8000")
    print(" [Swagger UI Docs] http://localhost:8000/docs")
    print(" [Health Check]    http://localhost:8000/health")
    print("=" * 65 + "\n")

    # Run uvicorn server pointing to app.main:app inside backend directory
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        app_dir=str(BACKEND_DIR)
    )
