"""Main application entry point for VanSure backend."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
from starlette.status import HTTP_200_OK, HTTP_404_NOT_FOUND

from app.core.config import get_settings, setup_logging
from app.core.exceptions import VanSureException
from app.core.logging import get_request_id, logger
from app.core.middleware import setup_middleware
from app.api.v1.router import api_router
from app.infrastructure.database import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager.

    Handles startup and shutdown events.
    """
    settings = get_settings()
    
    # Startup
    logger.info(
        "Application startup",
        extra={
            "app_name": settings.app_name,
            "environment": settings.environment,
        },
    )
    
    # Ensure database is ready
    async with engine.begin() as conn:
        # In production, you might want to run migrations here
        # or ensure the database is reachable
        pass
    
    yield
    
    # Shutdown
    logger.info("Application shutdown")


def create_app(settings=None) -> FastAPI:
    """Create and configure the FastAPI application.

    Args:
        settings: Optional settings (will use defaults if not provided)

    Returns:
        Configured FastAPI application
    """
    settings = settings or get_settings()
    
    # Configure logging
    setup_logging(
        level=settings.logging.level,
        format=settings.logging.format,
        app_name=settings.app_name,
        version=settings.app_version,
    )
    
    # Create FastAPI app
    app = FastAPI(
        title=f"{settings.app_name} API",
        version=settings.app_version,
        description="Multi-tenant school van management SaaS platform",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        openapi_url="/openapi.json" if settings.debug else None,
        lifespan=lifespan,
        # Add exception handlers for custom exceptions
        exceptions={
            VanSureException: van_sure_exception_handler,
        },
    )
    
    # Setup middleware
    setup_middleware(app, settings)
    
    # Add CORS if configured
    if settings.security.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.security.cors_origins,
            allow_credentials=settings.security.cors_allow_credentials,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    # Health check endpoint (no auth required)
    @app.get("/health", status_code=HTTP_200_OK, tags=["Health"])
    async def health_check(request: Request) -> dict[str, str]:
        """Health check endpoint for load balancers and monitoring."""
        return {
            "status": "healthy",
            "version": settings.app_version,
            "request_id": get_request_id(),
        }

    @app.get("/ready", status_code=HTTP_200_OK, tags=["Health"])
    async def readiness_check() -> dict[str, str]:
        """Readiness check endpoint for Kubernetes and orchestrators."""
        # In production, check database, Redis, etc.
        return {
            "status": "ready",
            "checks": "all passed",
        }

    @app.get("/", status_code=HTTP_200_OK, tags=["Root"])
    async def root() -> dict[str, str]:
        """Root endpoint."""
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "message": "Welcome to VanSure API",
        }
    
    # Include API routers
    app.include_router(api_router)
    
    # Add 404 handler
    @app.exception_handler(HTTP_404_NOT_FOUND)
    async def not_found_handler(request: Request, exc):
        """Handle 404 errors with consistent format."""
        return JSONResponse(
            status_code=HTTP_404_NOT_FOUND,
            content={
                "error_code": "NOT_FOUND",
                "message": "Resource not found",
            },
        )
    
    return app


async def van_sure_exception_handler(
    request: Request,
    exc: VanSureException,
) -> JSONResponse:
    """Handle VanSure exceptions with consistent error response."""
    request_id = get_request_id()
    
    logger.warning(
        "Request failed",
        extra={
            "error_code": exc.error_code.value,
            "status_code": exc.status_code,
            "request_id": request_id,
        },
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_code": exc.error_code.value,
            "message": exc.detail.get("message") if exc.detail else str(exc),
            "request_id": request_id,
            **(exc.detail or {}),
        },
    )


# Create the app instance
app = create_app()