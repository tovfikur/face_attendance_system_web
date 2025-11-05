"""
FastAPI application entry point.
"""

from datetime import datetime

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.logging import get_logger, setup_logging
from app.schemas.common import ErrorResponse, HealthStatus

# Setup logging
setup_logging()
logger = get_logger(__name__)


def create_app() -> FastAPI:
    """Create FastAPI application."""

    app = FastAPI(
        title=settings.APP_NAME,
        description="CCTV Face Attendance System Backend API",
        version=settings.APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # =========================================================================
    # MIDDLEWARE
    # =========================================================================

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=settings.ALLOW_CREDENTIALS,
        allow_methods=settings.ALLOWED_METHODS,
        allow_headers=settings.ALLOWED_HEADERS,
    )

    # Gzip compression middleware
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # =========================================================================
    # EXCEPTION HANDLERS
    # =========================================================================

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle general exceptions."""
        logger.error(f"Unhandled exception: {str(exc)}", exc_info=exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Internal server error",
                    "details": None,
                },
                "requestId": str(request.headers.get("x-request-id", "unknown")),
            },
        )

    # =========================================================================
    # HEALTH CHECK ENDPOINTS
    # =========================================================================

    @app.get("/health/live", tags=["Health"], summary="Liveness probe")
    async def health_live() -> HealthStatus:
        """Liveness probe endpoint for Kubernetes."""
        return HealthStatus(
            status="alive",
            timestamp=datetime.utcnow().isoformat(),
            version=settings.APP_VERSION,
        )

    @app.get("/health/ready", tags=["Health"], summary="Readiness probe")
    async def health_ready() -> HealthStatus:
        """Readiness probe endpoint for Kubernetes."""
        # TODO: Check database connection
        # TODO: Check Redis connection
        return HealthStatus(
            status="ready",
            timestamp=datetime.utcnow().isoformat(),
            version=settings.APP_VERSION,
        )

    @app.get("/", tags=["Root"])
    async def root():
        """Root endpoint."""
        return {
            "message": "Welcome to Face Attendance System API",
            "version": settings.APP_VERSION,
            "docs": "/docs",
            "redoc": "/redoc",
        }

    # =========================================================================
    # API ROUTES
    # =========================================================================

    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    # =========================================================================
    # STARTUP & SHUTDOWN
    # =========================================================================

    @app.on_event("startup")
    async def startup_event():
        """Run on application startup."""
        logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
        logger.info(f"Environment: {settings.ENVIRONMENT}")
        logger.info(f"Debug mode: {settings.DEBUG}")
        # TODO: Initialize database connection
        # TODO: Initialize Redis connection
        # TODO: Initialize MinIO connection

    @app.on_event("shutdown")
    async def shutdown_event():
        """Run on application shutdown."""
        logger.info(f"Shutting down {settings.APP_NAME}")
        # TODO: Close database connection
        # TODO: Close Redis connection
        # TODO: Close MinIO connection

    return app


# Create application instance
app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD and settings.DEBUG,
        workers=settings.WORKERS if not settings.DEBUG else 1,
    )
