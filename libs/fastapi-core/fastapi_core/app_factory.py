from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from ._build_info import BUILD_TIME
from ._version import __version__
from .config import OPEN_API_ENABLED, configure_logging
from .exceptions.exception_handler import register_exception_handlers
from .middlewares import (
    LogContextMiddleware,
    ResponseTimeMiddleware,
    SecurityHeadersMiddleware,
)


def create_app(app_name: str, lifespan=None) -> FastAPI:  # type: ignore
    """
    Factory function to create a FastAPI application instance.

    Args:
    ----
        app_name (str): The name of the application for logging and identification.
        lifespan: A callable that returns a Lifespan instance
        for managing the app's lifespan events.

    Returns:
    -------
        FastAPI: Configured FastAPI application instance.

    """
    # Create FastAPI app instance
    app = FastAPI(
        default_response_class=ORJSONResponse,
        docs_url="/openapi" if OPEN_API_ENABLED else None,
        redoc_url="/redoc" if OPEN_API_ENABLED else None,
        openapi_url="/openapi-json" if OPEN_API_ENABLED else None,
        lifespan=lifespan,
    )

    configure_logging(app_name)

    # Add middlewares
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(ResponseTimeMiddleware)
    app.add_middleware(LogContextMiddleware)
    app.add_middleware(CorrelationIdMiddleware)  # This must be below LoggerMiddleware

    register_exception_handlers(app)

    # Root Endpoint for Health and Liveness Check.
    @app.get("/", summary="Root Endpoint", tags=["Health Check"])
    def root() -> dict[str, str]:
        return {"build": f"{__version__}/{BUILD_TIME}"}

    return app
