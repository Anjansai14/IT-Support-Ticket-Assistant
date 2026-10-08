# Intelligent IT Support Ticket Assistant ⚡

An AI-powered helpdesk automation platform and ticketing assistant built with **FastAPI**, **SQLite**, and an interactive modern web dashboard. Features automated AI triage (category classification, priority assignment, team routing, and ticket summaries) with a resilient rule-based fallback.

---

## 📂 Project Architecture

The repository is cleanly decoupled into dedicated backend and frontend modules:

```text
it-support-ticket-assistant/
│
├── backend/                           # FastAPI Application & API services
│   ├── app/
│   │   ├── config.py                  # App settings & environment loading
│   │   ├── database.py                # SQLAlchemy engine & session
│   │   ├── main.py                    # Server entrypoint & static mount
│   │   ├── models.py                  # Database ORM models
│   │   ├── schemas.py                 # Pydantic validation schemas
│   │   ├── routes/tickets.py          # REST endpoints (CRUD, analytics, AI)
│   │   ├── services/ai_service.py     # OpenAI client & fallback triage
│   │   └── utils/prompts.py           # Classification prompt templates
│   ├── tests/                         # Pytest automated test suite (13 tests)
│   ├── requirements.txt               # Backend Python dependencies
│   ├── .env.example                   # Environment configuration template
│   └── tickets.db                     # SQLite database (auto-generated)
│
├── frontend/                          # Client Web Interface
│   ├── index.html                     # Responsive helpdesk dashboard
│   ├── css/styles.css                 # Glassmorphic dark theme styles
│   └── js/app.js                      # Dynamic UI logic, search & ticket triage
│
├── Dockerfile                         # Production container specification
├── run.bat                            # 1-Click launcher for Windows CMD / Explorer
├── run.ps1                            # 1-Click launcher for PowerShell
└── README.md
```

---

## 🚀 Getting Started in VS Code (After Git Clone)

When you clone a repository from Git, the Python virtual environment (`.venv`) and `.env` files are not included by design (they are ignored by Git). Follow these steps to run the project:

### Method 1: Automatic 1-Click Setup (Recommended)

In your VS Code terminal (or by double-clicking the file in File Explorer), run:

```bat
.\run.bat
```
*(or in PowerShell: `.\run.ps1`)*

> **What this does automatically:**
> 1. Detects if `.venv` is missing and creates it (`python -m venv .venv`).
> 2. Installs all required packages from `backend/requirements.txt`.
> 3. Creates `backend/.env` from `backend/.env.example`.
> 4. Starts the server at **http://localhost:8000** with hot reload.

---

### Method 2: Manual Setup in VS Code Terminal

If you prefer to configure manually:

#### 1. Open the Project in VS Code
Open the root `it-support-ticket-assistant` folder in VS Code (`File > Open Folder...`).

#### 2. Create and Activate Virtual Environment
In the VS Code terminal (PowerShell):
```powershell
# Create virtual environment
python -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1
```
*(If on Command Prompt `cmd`):*
```cmd
.\.venv\Scripts\activate.bat
```

#### 3. Install Dependencies
```bash
pip install --upgrade pip
pip install -r backend/requirements.txt
```

#### 4. Configure Environment
Copy the example environment file:
```bash
cp backend/.env.example backend/.env
```
*(Optional: Add your `OPENAI_API_KEY` in `backend/.env` for live OpenAI triage. If not provided, the system automatically uses the intelligent rule-based triage fallback).*

#### 5. Select Python Interpreter in VS Code
1. Press `Ctrl + Shift + P` (or `Cmd + Shift + P` on Mac).
2. Type **`Python: Select Interpreter`**.
3. Choose the interpreter with `('.venv': venv)`: `.\.venv\Scripts\python.exe`.

#### 6. Run the Server
From the `backend/` directory:
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 🌐 Access the Application

Once running, open your web browser:

| Interface | URL | Description |
| :--- | :--- | :--- |
| **Web Dashboard** | [http://localhost:8000](http://localhost:8000) | Interactive Helpdesk UI to submit and manage tickets |
| **Swagger UI** | [http://localhost:8000/docs](http://localhost:8000/docs) | Interactive OpenAPI documentation & test sandbox |
| **ReDoc** | [http://localhost:8000/redoc](http://localhost:8000/redoc) | Detailed API reference specifications |
| **Health Check** | [http://localhost:8000/health](http://localhost:8000/health) | Uptime and service status verification |

---

## 🧪 Running Automated Tests

Run the full pytest test suite from the `backend/` directory:

```powershell
cd backend
pytest -v
```

All 13 unit and integration tests run against an isolated in-memory SQLite database with mocked AI endpoints.

---

## 🐳 Docker Deployment

To build and run using Docker:

```bash
docker build -t it-support-ticket-assistant .
docker run -p 8000:8000 it-support-ticket-assistant
```