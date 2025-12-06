"""Middleware for automatic metrics collection."""

import logging
import time
from typing import Callable, Optional

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from fastapi_core.metrics import (
    http_requests_in_progress,
    record_auth_attempt,
    record_auth_failure,
    record_http_request,
)


logger = logging.getLogger(__name__)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware for collecting HTTP metrics."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and record metrics.

        Args:
        ----
            request: Incoming request
            call_next: Next middleware/handler

        Returns:
        -------
            Response with metrics recorded

        """
        # Extract request information
        method = request.method
        endpoint = request.url.path

        # Try to extract tenant_id if available
        tenant_id: Optional[str] = None
        try:
            # Tenant ID is extracted from JWT token in request scope
            if hasattr(request, "scope") and "user" in request.scope:
                user = request.scope["user"]
                if hasattr(user, "tenant_id"):
                    tenant_id = user.tenant_id
        except Exception as e:
            logger.debug(f"Could not extract tenant_id: {e}")

        # Record request in progress
        http_requests_in_progress.labels(method=method, endpoint=endpoint).inc()

        start_time = time.time()
        status_code = 500  # Default to server error

        try:
            # Process request
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception as e:
            logger.error(f"Error processing request {method} {endpoint}: {e}")
            status_code = 500
            raise
        finally:
            # Calculate duration
            duration_seconds = time.time() - start_time

            # Record metrics
            record_http_request(
                method=method,
                endpoint=endpoint,
                status_code=status_code,
                duration_seconds=duration_seconds,
                tenant_id=tenant_id,
            )

            # Record request no longer in progress
            http_requests_in_progress.labels(method=method, endpoint=endpoint).dec()

            logger.debug(f"{method} {endpoint} - {status_code} ({duration_seconds*1000:.1f}ms)")


class AuthenticationMetricsMiddleware(BaseHTTPMiddleware):
    """Middleware for tracking authentication metrics."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and record auth metrics.

        Args:
        ----
            request: Incoming request
            call_next: Next middleware/handler

        Returns:
        -------
            Response with auth metrics recorded

        """
        # Check if endpoint requires authentication
        if request.url.path.startswith("/health") or request.url.path == "/docs":
            return await call_next(request)

        # Attempt to process request
        try:
            response = await call_next(request)

            # Record auth attempt result
            if response.status_code in [200, 201, 204]:
                record_auth_attempt("jwt", "success")
            elif response.status_code == 401:
                record_auth_failure("jwt", "invalid_token")
            elif response.status_code == 403:
                record_auth_failure("jwt", "insufficient_permissions")

            return response
        except Exception as e:
            logger.error(f"Auth error: {e}")
            record_auth_failure("jwt", "auth_error")
            raise
