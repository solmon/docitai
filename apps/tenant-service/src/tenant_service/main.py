"""Tenant service FastAPI application entry point."""

import logging
import os
from pathlib import Path

from database_core.connection import DatabaseManager
from fastapi import FastAPI, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi_core.app_factory import create_app

from tenant_service.api.v1 import storage, tenants, retention_policies, compliance_audit, folders, master_data_proper, health, metrics
from tenant_service.config import settings
from tenant_service.exceptions import ErrorResponse, TenantServiceException

# Configure logging
logger = logging.getLogger(__name__)


def create_application() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Uses fastapi-core's app_factory for consistent configuration across all services.
    Integrates database, authentication, and error handling middleware.
    """
    # Create base app using fastapi-core factory
    app = create_app("tenant-service")

    # Add tenant service specific configuration
    app.title = "Tenant Management Service"
    app.version = "0.1.0"
    app.description = "Core microservice for tenant onboarding, storage configuration, compliance, and master data"

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Metrics middleware is now included in create_app() with enable_metrics=True by default

    # Initialize database on startup
    @app.on_event("startup")
    async def startup():
        """Initialize database connections and tables on application startup."""
        try:
            DatabaseManager.initialize(
                database_url=settings.database.database_url,
                database_type=settings.database.database_type,
                echo_sql=settings.database.echo_sql,
            )
            DatabaseManager.create_db_and_tables()
            logger.info("Application startup completed successfully - database initialized")
        except ModuleNotFoundError as e:
            if "psycopg2" in str(e):
                logger.warning("psycopg2 not installed - database initialization skipped (development mode)")
                logger.info("Application startup completed - running in development mode without database")
            else:
                logger.error(f"Failed to initialize database: {e}")
                raise
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    @app.on_event("shutdown")
    async def shutdown():
        """Close database connections on application shutdown."""
        DatabaseManager.close()
        logger.info("Application shutdown completed")

    # Exception handlers
    @app.exception_handler(TenantServiceException)
    async def tenant_service_exception_handler(request, exc: TenantServiceException):
        """Handle tenant service exceptions."""
        error_response = ErrorResponse(
            error_code=exc.error_code,
            message=exc.message,
            details=exc.details,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response.dict(),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request, exc: RequestValidationError):
        """Handle Pydantic validation errors."""
        error_response = ErrorResponse(
            error_code="VALIDATION_ERROR",
            message="Invalid request data",
            details={"errors": exc.errors()},
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error_response.dict(),
        )

    logger.info("Tenant service initialized with all middleware and error handlers")

    # Include API routers
    app.include_router(health.router)
    app.include_router(metrics.router)
    app.include_router(tenants.router)
    app.include_router(storage.router)
    app.include_router(retention_policies.router)
    app.include_router(compliance_audit.router)
    app.include_router(folders.router)
    app.include_router(master_data_proper.router)

    return app


# Create the application instance
app = create_application()


@app.get("/")
async def root():
    """Root endpoint."""
    return {"service": "Tenant Management Service", "version": "0.1.0", "docs": "/docs"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
