"""
Main application module and entry point for the FastAPI server.
"""
import os
from pathlib import Path
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from app.config import settings
from app.database import engine, Base
import app.models as models
from app.routes import tickets
from app.exceptions import setup_exception_handlers

# Configure standard logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("it-support-ticket-assistant")

# Locate separate frontend directory
FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"
if not FRONTEND_DIR.exists():
    FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"



@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager for startup and shutdown events.
    Creates database tables if they do not exist.
    """
    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables verified/created successfully.")
    yield
    logger.info("Shutting down application...")


# OpenAPI tag descriptions for interactive documentation
tags_metadata = [
    {
        "name": "Tickets",
        "description": "IT support ticket lifecycle operations, automated AI triage, queue filtering, and operations analytics."
    },
    {
        "name": "Health",
        "description": "System health and liveness monitoring endpoints."
    },
    {
        "name": "General",
        "description": "Service metadata, version info, and API documentation links."
    }
]

# Initialize FastAPI application instance
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.PROJECT_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=tags_metadata,
    lifespan=lifespan
)

# Configure CORS (Cross-Origin Resource Sharing) for client integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register route modules
app.include_router(tickets.router, prefix="/tickets", tags=["Tickets"])

# Register centralized exception handlers
setup_exception_handlers(app)

# Mount separate frontend assets directory
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")
    if (FRONTEND_DIR / "css").exists():
        app.mount("/css", StaticFiles(directory=str(FRONTEND_DIR / "css")), name="css")
    if (FRONTEND_DIR / "js").exists():
        app.mount("/js", StaticFiles(directory=str(FRONTEND_DIR / "js")), name="js")


@app.get("/", tags=["General"])
def root(request: Request):
    """
    Root endpoint serving interactive web UI dashboard, or API metadata for JSON clients.
    """
    index_file = FRONTEND_DIR / "index.html"
    accept_header = request.headers.get("accept", "")
    
    # If explicitly requested JSON only without html support
    if "application/json" in accept_header and "text/html" not in accept_header:
        return {
            "message": f"Welcome to {settings.PROJECT_NAME}",
            "version": settings.PROJECT_VERSION,
            "docs_url": "/docs",
            "health_check": "/health"
        }

    # Serve the visual web dashboard
    if index_file.exists():
        return FileResponse(index_file)

    return {
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "version": settings.PROJECT_VERSION,
        "docs_url": "/docs",
        "health_check": "/health"
    }


@app.get("/health", tags=["Health"])
def health_check():
    """
    Health check endpoint for liveness and uptime monitoring.
    """
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.PROJECT_VERSION
    }
