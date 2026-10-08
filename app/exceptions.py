"""
Global exception handlers and custom error response formatting.
"""
import logging
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import SQLAlchemyError
from app.services.ai_service import AIServiceError

logger = logging.getLogger("it-support-ticket-assistant")


def setup_exception_handlers(app: FastAPI) -> None:
    """
    Register centralized exception handlers on the FastAPI application instance.
    """

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """
        Catches Pydantic schema validation failures and formats user-friendly error messages.
        """
        error_details = []
        for error in exc.errors():
            # Extract clean field location path
            field = " -> ".join(str(loc) for loc in error.get("loc", []) if loc != "body")
            message = error.get("msg", "Invalid value")
            error_details.append({
                "field": field or "body",
                "message": message
            })

        logger.warning(f"Validation failed on {request.method} {request.url.path}: {error_details}")
        return JSONResponse(
            status_code=422,
            content={
                "error_code": "VALIDATION_ERROR",
                "detail": "Input validation failed. Please check the supplied fields.",
                "errors": error_details
            }
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        """
        Catches standard HTTPExceptions (e.g., 404 Not Found, 400 Bad Request).
        """
        logger.info(f"HTTP {exc.status_code} on {request.method} {request.url.path}: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error_code": f"HTTP_{exc.status_code}",
                "detail": exc.detail
            }
        )

    @app.exception_handler(AIServiceError)
    async def ai_service_exception_handler(request: Request, exc: AIServiceError):
        """
        Catches all OpenAI and AI triage errors without leaking secrets or raw stack traces.
        """
        logger.error(f"AI Service Exception on {request.method} {request.url.path}: {exc.message}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error_code": "AI_SERVICE_ERROR",
                "detail": exc.message
            }
        )

    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
        """
        Catches database errors and prevents SQL query leaks to the client.
        """
        logger.error(f"Database error on {request.method} {request.url.path}: {str(exc)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error_code": "DATABASE_ERROR",
                "detail": "A database operation failed. Please try again or contact IT support."
            }
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        """
        Catch-all handler for unhandled server exceptions.
        """
        logger.exception(f"Unhandled exception on {request.method} {request.url.path}: {str(exc)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error_code": "INTERNAL_SERVER_ERROR",
                "detail": "An unexpected error occurred while processing your request."
            }
        )
