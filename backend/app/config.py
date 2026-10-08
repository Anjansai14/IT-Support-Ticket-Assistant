"""
Application configuration management using environment variables.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory pointing to project root
BASE_DIR = Path(__file__).resolve().parent.parent

# Explicitly load environment variables from the root .env file
load_dotenv(dotenv_path=BASE_DIR / ".env")


class Settings:
    """Application configuration settings."""
    PROJECT_NAME: str = "Intelligent IT Support Ticket Assistant"
    PROJECT_VERSION: str = "1.0.0"
    PROJECT_DESCRIPTION: str = (
        "AI-powered IT support ticket management and automated triage system."
    )

    # Database configuration (defaults to local SQLite)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./tickets.db")

    # OpenAI configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


settings = Settings()
