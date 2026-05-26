"""Main FastAPI application entry point."""

import asyncio
import sys

# Set event loop policy for Windows before any asyncio calls
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exception_handlers import request_validation_exception_handler
from pydantic import ValidationError

from app.core.config import get_settings
from app.core.logging import setup_logging, get_logger
from app.core.database import init_db, close_db
from app.core.exceptions import AppException

# Import routers
from app.routers import auth_router, listing_router, booking_router, listing_image_router

settings = get_settings()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.
    
    Handles startup and shutdown events:
    - Setup logging
    - Initialize database connections
    - Cleanup on shutdown
    """
    # Startup
    setup_logging()
    logger.info("Starting up CouchSurfing API")
    
    # Initialize database (in production, use Alembic migrations instead)
    # Temporarily disabled due to connection issues
    # if settings.DEBUG:
    #     await init_db()
    #     logger.info("Database initialized (DEBUG mode)")
    
    yield
    
    # Shutdown
    await close_db()
    logger.info("Shutting down CouchSurfing API")


def create_app() -> FastAPI:
    """
    Application factory for creating FastAPI instance.
    
    Returns:
        Configured FastAPI application
    """
    app = FastAPI(
        title=settings.APP_NAME,
        description="P2P accommodation exchange platform API",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Register exception handlers (должны быть зарегистрированы перед CORS middleware)
    register_exception_handlers(app)

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    # Auth router already has /auth prefix internally, so we use /api/v1 as main prefix
    app.include_router(auth_router, prefix="/api/v1", tags=["Authentication"])
    app.include_router(listing_router, prefix="/api/v1", tags=["Listings"])
    app.include_router(booking_router, prefix="/api/v1", tags=["Bookings"])
    app.include_router(listing_image_router, prefix="/api/v1", tags=["Listing Images"])
    # Future routers:
    # app.include_router(reviews.router, prefix="/api/v1/reviews", tags=["Reviews"])
    # app.include_router(messages.router, prefix="/api/v1/messages", tags=["Messages"])

    # Serve static files (uploaded images)
    import os
    from fastapi.staticfiles import StaticFiles
    
    # Ensure uploads directory exists - use absolute path to backend/uploads (where files are actually saved)
    uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
    os.makedirs(uploads_dir, exist_ok=True)
    
    app.mount("/static", StaticFiles(directory=uploads_dir), name="static")

    # Health check endpoint
    @app.get("/health", tags=["Health"])
    async def health_check():
        """Check if the API is running."""
        return {"status": "healthy", "version": "1.0.0"}

    logger.info("FastAPI application created successfully")
    return app


def get_cors_headers(request: Request) -> dict:
    """Get CORS headers matching the request origin."""
    ALLOWED_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]
    origin = request.headers.get("origin")
    if origin in ALLOWED_ORIGINS:
        allow_origin = origin
    else:
        allow_origin = ALLOWED_ORIGINS[0] if ALLOWED_ORIGINS else ""
    return {
        "Access-Control-Allow-Origin": allow_origin,
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "*",
    }


def register_exception_handlers(app: FastAPI) -> None:
    """
    Register global exception handlers.
    
    Provides consistent error response format across the application.
    CORS headers are added manually because exception handlers bypass
    the CORS middleware response processing.
    """

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        """Handle custom application exceptions."""
        logger.warning(
            "Application exception",
            path=request.url.path,
            method=request.method,
            exception=str(exc),
            status_code=exc.status_code,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "message": exc.message,
                    "detail": exc.detail,
                    "type": type(exc).__name__,
                }
            },
            headers=get_cors_headers(request),
        )

    @app.exception_handler(ValidationError)
    async def validation_exception_handler(request: Request, exc: ValidationError):
        """Handle Pydantic validation errors."""
        # Sanitize errors: remove raw SQLAlchemy objects from input_value
        # to avoid "Object is not JSON serializable" errors
        errors = []
        for err in exc.errors():
            err_copy = dict(err)
            if "input" in err_copy:
                inp = err_copy["input"]
                if hasattr(inp, "__class__") and not isinstance(inp, (str, int, float, bool, list, dict, type(None))):
                    err_copy["input"] = str(inp)
                elif isinstance(inp, list):
                    err_copy["input"] = [
                        str(item) if hasattr(item, "__class__") and not isinstance(item, (str, int, float, bool, dict, type(None))) else item
                        for item in inp
                    ]
            errors.append(err_copy)

        logger.warning(
            "Validation error",
            path=request.url.path,
            errors=errors,
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "message": "Validation error",
                    "detail": errors,
                    "type": "ValidationError",
                }
            },
            headers=get_cors_headers(request),
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle unexpected exceptions."""
        logger.error(
            "Unexpected exception",
            path=request.url.path,
            method=request.method,
            exception=str(exc),
            exc_info=True,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "message": "Internal server error",
                    "detail": "An unexpected error occurred",
                    "type": type(exc).__name__,
                }
            },
            headers=get_cors_headers(request),
        )


# Create application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info",
    )
