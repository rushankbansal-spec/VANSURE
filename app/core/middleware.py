"""FastAPI middleware for request processing."""

import time
import uuid
from contextlib import asynccontextmanager
from typing import Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.base import BaseHTTPMiddleware, ResponseFunction
from starlette.types import ASGIApp

from app.core.config import Settings, get_security_settings
from app.core.tenant_context import TenantContext


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add a unique request ID to each request."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add request ID header and continue processing."""
        # Check for existing request ID (for retries)
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

        # Add to scope for downstream access
        request.state.request_id = request_id

        # Add to response
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id

        return response


class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """Middleware for correlation ID propagation."""

    def __init__(self, app: ASGIApp, header_name: str = "X-Correlation-ID") -> None:
        """Initialize middleware.

        Args:
            app: The ASGI application
            header_name: Name of the correlation ID header
        """
        super().__init__(app)
        self.header_name = header_name

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add correlation ID to request and response."""
        correlation_id = request.headers.get(
            self.header_name, str(uuid.uuid4())
        )

        # Add to state and response
        request.state.correlation_id = correlation_id

        response = await call_next(request)
        response.headers[self.header_name] = correlation_id

        return response


class TenantContextMiddleware(BaseHTTPMiddleware):
    """Middleware to extract and set tenant context from authenticated requests.

    This middleware:
    1. Extracts tenant context from validated JWT (handled by auth middleware)
    2. Sets it in the context variables for database queries
    3. Ensures clean-up after request
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with tenant context."""
        try:
            # Tenant context should already be set by auth middleware
            # This middleware can also be used standalone for testing
            response = await call_next(request)
            return response
        finally:
            # Clean up context after request
            TenantContext.clear()


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add security headers to response."""
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
        response.headers["Pragma"] = "no-cache"

        # Strict Transport Security (only in production with HTTPS)
        settings = Settings()
        if settings.is_production:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )

        # Content Security Policy (if configured)
        security_settings = get_security_settings()
        if security_settings.content_security_policy:
            response.headers["Content-Security-Policy"] = (
                security_settings.content_security_policy
            )

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using Redis."""

    def __init__(self, app: ASGIApp, redis_client: Any) -> None:
        """Initialize rate limit middleware.

        Args:
            app: The ASGI application
            redis_client: Redis async client instance
        """
        super().__init__(app)
        self.redis = redis_client

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Check rate limits and process request."""
        # Rate limiting logic would go here
        # For now, just pass through
        response = await call_next(request)
        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for structured request logging."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log request details."""
        start_time = time.time()

        # Log request start
        request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
        correlation_id = getattr(request.state, "correlation_id", None)

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000

        # Log completion (structured logging would go here)
        # logger.info("request_complete", extra={...})

        return response


def setup_middleware(app: FastAPI, settings: Settings) -> None:
    """Configure middleware for the FastAPI application.

    Args:
        app: FastAPI application instance
        settings: Application settings
    """
    security_settings = get_security_settings()

    # Security headers first (before other middleware)
    app.add_middleware(SecurityHeadersMiddleware)

    # Request ID and correlation ID
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(CorrelationIDMiddleware)

    # CORS configuration
    if security_settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=security_settings.cors_origins,
            allow_credentials=security_settings.cors_allow_credentials,
            allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
            allow_headers=["*"],
            max_age=security_settings.cors_max_age,
        )

    # Gzip compression for responses
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # Tenant context
    app.add_middleware(TenantContextMiddleware)

    # Logging
    app.add_middleware(LoggingMiddleware)


# Context manager for tenant context in non-request contexts
@asynccontextmanager
async def tenant_context(tenant_id: str, user_id: str | None = None):
    """Context manager for setting tenant context.

    Usage:
        async with tenant_context("school-123"):
            await student_repo.get_by_id(student_id)
    """
    TenantContext.set_tenant(tenant_id, user_id)
    try:
        yield
    finally:
        TenantContext.clear()