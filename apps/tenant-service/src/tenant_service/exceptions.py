"""Exception handling and error responses for tenant service."""

import logging
from typing import Any, Optional

from fastapi import status
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ErrorResponse(BaseModel):
    """Standardized error response format."""

    error_code: str
    message: str
    details: Optional[dict[str, Any]] = None
    request_id: Optional[str] = None

    class Config:
        from_attributes = True


class TenantServiceException(Exception):
    """Base exception for tenant service."""

    def __init__(
        self,
        error_code: str,
        message: str,
        details: Optional[dict] = None,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    ):
        self.error_code = error_code
        self.message = message
        self.details = details or {}
        self.status_code = status_code
        super().__init__(message)


class ResourceNotFoundError(TenantServiceException):
    """Resource not found error."""

    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            error_code="RESOURCE_NOT_FOUND",
            message=f"{resource_type} not found: {resource_id}",
            details={"resource_type": resource_type, "resource_id": resource_id},
            status_code=status.HTTP_404_NOT_FOUND,
        )


class TenantIsolationViolationError(TenantServiceException):
    """Tenant isolation violation error."""

    def __init__(self, user_tenant_id: str, resource_tenant_id: str):
        super().__init__(
            error_code="TENANT_ISOLATION_VIOLATION",
            message="User cannot access resource in different tenant",
            details={
                "user_tenant_id": user_tenant_id,
                "resource_tenant_id": resource_tenant_id,
            },
            status_code=status.HTTP_403_FORBIDDEN,
        )


class ValidationError(TenantServiceException):
    """Validation error for invalid input."""

    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(
            error_code="VALIDATION_ERROR",
            message=message,
            details=details,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


class PermissionDeniedError(TenantServiceException):
    """Permission denied error."""

    def __init__(self, reason: str = "Insufficient permissions"):
        super().__init__(
            error_code="PERMISSION_DENIED",
            message=reason,
            status_code=status.HTTP_403_FORBIDDEN,
        )


class StorageProviderError(TenantServiceException):
    """Storage provider error."""

    def __init__(self, provider_type: str, message: str, details: Optional[dict] = None):
        super().__init__(
            error_code="STORAGE_PROVIDER_ERROR",
            message=f"Storage provider error ({provider_type}): {message}",
            details={"provider_type": provider_type, **(details or {})},
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


async def exception_handler(exc: TenantServiceException) -> ErrorResponse:
    """
    Handle tenant service exceptions and convert to error responses.

    Args:
        exc: TenantServiceException instance

    Returns:
        ErrorResponse formatted error
    """
    logger.error(f"Service error: {exc.error_code} - {exc.message}", extra={"details": exc.details})

    return ErrorResponse(
        error_code=exc.error_code,
        message=exc.message,
        details=exc.details,
    )
