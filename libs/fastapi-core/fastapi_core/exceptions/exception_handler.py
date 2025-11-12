# mypy: disable-error-code="arg-type"

from http import HTTPStatus

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import ORJSONResponse
from sqlalchemy.exc import DBAPIError, IntegrityError, ProgrammingError
from starlette.exceptions import HTTPException as StarletteHTTPException

from fastapi_core.config import APP_ENV, AppEnv, get_logger

from .error_code import ErrorCode


logger = get_logger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    """Registers global exception handlers for the FastAPI application."""
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, starlette_http_exception_handler)
    app.add_exception_handler(RequestValidationError, request_validation_exception_handler)
    app.add_exception_handler(DBAPIError, db_operation_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)


async def http_exception_handler(_: Request, exc: HTTPException) -> ORJSONResponse:
    """Handles FastAPI's HTTPException. Most of these are exceptions from exception_4xx and exception_5xx."""
    detail = (
        exc.detail
        if isinstance(exc.detail, dict) and "error" in exc.detail and "error_code" in exc.detail
        else {"error": exc.detail, "error_code": ErrorCode.UNCLASSIFIED}
    )
    return ORJSONResponse(
        status_code=exc.status_code,
        content={
            "error": detail.get("error", "Unhandled request error occurred"),
            "error_code": detail.get("error_code", ErrorCode.UNCLASSIFIED),
        },
    )


async def starlette_http_exception_handler(request: Request, exc: StarletteHTTPException) -> ORJSONResponse:
    """Handles Starlette's HTTPException. Provides specific handling for 404 errors."""
    # HTTP URL not found
    if exc.status_code == HTTPStatus.NOT_FOUND:
        return ORJSONResponse(
            status_code=HTTPStatus.NOT_FOUND,
            content={
                "error": f"{request.url.path} path not found",
                "error_code": ErrorCode.PATH_NOT_FOUND,
            },
        )
    # For other HTTP exceptions, defer to the HTTPException handler
    return await http_exception_handler(request, exc)


async def request_validation_exception_handler(_: Request, exc: RequestValidationError) -> ORJSONResponse:
    """Handles request validation errors (e.g., invalid request payloads or query params)."""
    return ORJSONResponse(
        status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        content={
            "error": exc.errors(),
            "error_code": ErrorCode.REQUEST_VALIDATION,
        },
    )


async def db_operation_exception_handler(_: Request, exc: DBAPIError) -> ORJSONResponse:
    """Handles database operation errors"""
    logger.error("Database operation failed: %s", exc, exc_info=APP_ENV == AppEnv.DEVELOPMENT)
    # Customize response based on the specific exception type
    if isinstance(exc, IntegrityError):
        error = "Integrity error: possible constraint violation"
        status_code = HTTPStatus.BAD_REQUEST
    elif isinstance(exc, ProgrammingError):
        error = "Programming error from database"
        status_code = HTTPStatus.INTERNAL_SERVER_ERROR
    else:
        error = "Database operation failed"
        status_code = HTTPStatus.INTERNAL_SERVER_ERROR

    return ORJSONResponse(
        status_code=status_code,
        content={
            "error": error,
            "error_code": ErrorCode.DATABASE_API_OPERATION,
        },
    )


async def generic_exception_handler(_: Request, exc: Exception) -> ORJSONResponse:
    """
    Handles all uncaught exceptions. Logs the error and returns a generic response.
    THIS SHOULD BE MINIMAL TO ZERO IN PRODUCTION.
    """
    logger.error("Unhandled exception occurred: %s", exc, exc_info=APP_ENV == AppEnv.DEVELOPMENT)
    return ORJSONResponse(
        status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        content={
            "error": "An unexpected error occurred",
            "error_code": ErrorCode.UNCLASSIFIED,
        },
    )
