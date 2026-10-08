"""
Main application module and entry point for the FastAPI server.
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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


@app.get("/", tags=["General"])
def root():
    """
    Root endpoint providing welcome metadata and documentation links.
    """
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
