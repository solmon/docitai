"""Distributed tracing middleware for FastAPI.

This middleware automatically:
- Creates spans for incoming HTTP requests
- Extracts trace context from headers
- Adds request/response attributes to spans
- Propagates trace context to downstream services
"""

import logging
import time
from typing import Callable, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from opentelemetry.trace import SpanKind

from tenant_service.infrastructure.tracing import (
    create_span,
    add_span_attributes,
    add_span_event,
    set_span_status,
    extract_context_from_headers,
    get_trace_id,
)

logger = logging.getLogger(__name__)


class TracingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that creates spans for HTTP requests.

    Features:
    - Automatic span creation for all requests
    - Context propagation from incoming headers
    - Request/response attribute recording
    - Error tracking and status reporting
    - Tenant context extraction from JWT
    """

    def __init__(
        self,
        app: ASGIApp,
        excluded_paths: Optional[list[str]] = None,
    ):
        """
        Initialize the tracing middleware.

        Args:
            app: ASGI application
            excluded_paths: Paths to exclude from tracing (e.g., /health, /metrics)
        """
        super().__init__(app)
        self.excluded_paths = excluded_paths or ["/health", "/health/ready", "/health/detailed", "/metrics"]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request with tracing.

        Args:
            request: Incoming FastAPI request
            call_next: Next middleware/handler in chain

        Returns:
            Response from the handler
        """
        # Skip tracing for excluded paths
        if request.url.path in self.excluded_paths:
            return await call_next(request)

        # Extract trace context from headers
        headers = dict(request.headers)
        extract_context_from_headers(headers)  # Sets up trace context

        # Build span name
        span_name = f"{request.method} {request.url.path}"

        # Extract tenant_id from authorization header if present
        tenant_id = self._extract_tenant_id(request)

        # Build initial attributes
        attributes = {
            "http.method": request.method,
            "http.url": str(request.url),
            "http.route": request.url.path,
            "http.scheme": request.url.scheme,
            "http.host": request.url.hostname or "unknown",
            "http.user_agent": request.headers.get("user-agent", "unknown"),
            "http.client_ip": self._get_client_ip(request),
        }

        if tenant_id:
            attributes["tenant.id"] = tenant_id

        start_time = time.time()

        with create_span(span_name, kind=SpanKind.SERVER, attributes=attributes, tenant_id=tenant_id):
            try:
                # Add trace ID to request state for logging
                request.state.trace_id = get_trace_id()

                # Add event for request start
                add_span_event(
                    "request.start",
                    {
                        "content_type": request.headers.get("content-type", "unknown"),
                        "content_length": request.headers.get("content-length", "0"),
                    },
                )

                # Call the next handler
                response = await call_next(request)

                # Calculate duration
                duration_ms = (time.time() - start_time) * 1000

                # Add response attributes
                add_span_attributes(
                    {
                        "http.status_code": response.status_code,
                        "http.response_content_type": response.headers.get("content-type", "unknown"),
                        "http.duration_ms": duration_ms,
                    }
                )

                # Set span status based on response code
                if response.status_code >= 500:
                    set_span_status(False, f"Server error: {response.status_code}")
                elif response.status_code >= 400:
                    set_span_status(False, f"Client error: {response.status_code}")
                else:
                    set_span_status(True, "OK")

                # Add event for request end
                add_span_event(
                    "request.end",
                    {
                        "status_code": response.status_code,
                        "duration_ms": duration_ms,
                    },
                )

                # Add trace ID to response headers for correlation
                trace_id = get_trace_id()
                if trace_id:
                    response.headers["X-Trace-ID"] = trace_id

                return response

            except Exception as e:
                # Record exception in span
                duration_ms = (time.time() - start_time) * 1000
                add_span_attributes(
                    {
                        "error": True,
                        "error.type": type(e).__name__,
                        "error.message": str(e),
                        "http.duration_ms": duration_ms,
                    }
                )
                set_span_status(False, str(e))
                add_span_event(
                    "exception",
                    {
                        "exception.type": type(e).__name__,
                        "exception.message": str(e),
                    },
                )
                raise

    def _extract_tenant_id(self, request: Request) -> Optional[str]:
        """
        Extract tenant ID from the request.

        Attempts to extract from:
        1. X-Tenant-ID header
        2. JWT token claims
        3. Path parameters (if present)

        Args:
            request: FastAPI request

        Returns:
            Tenant ID if found, None otherwise
        """
        # Try X-Tenant-ID header first
        tenant_id = request.headers.get("x-tenant-id")
        if tenant_id:
            return tenant_id

        # Try to extract from path for tenant-specific endpoints
        path_parts = request.url.path.split("/")
        try:
            if "tenants" in path_parts:
                tenant_index = path_parts.index("tenants") + 1
                if tenant_index < len(path_parts) and path_parts[tenant_index]:
                    return path_parts[tenant_index]
        except (ValueError, IndexError):
            pass

        return None

    def _get_client_ip(self, request: Request) -> str:
        """
        Get the client IP address from the request.

        Handles X-Forwarded-For header for proxied requests.

        Args:
            request: FastAPI request

        Returns:
            Client IP address
        """
        # Check for X-Forwarded-For header (reverse proxy)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        # Check for X-Real-IP header
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        # Fall back to direct client IP
        if request.client:
            return request.client.host

        return "unknown"


class DatabaseTracingMiddleware:
    """
    Context manager for tracing database operations.

    Usage:
        with DatabaseTracingMiddleware("SELECT", "tenants"):
            result = await db.execute(query)
    """

    def __init__(
        self,
        operation: str,
        table: str,
        tenant_id: Optional[str] = None,
    ):
        """
        Initialize database tracing context.

        Args:
            operation: Database operation type (SELECT, INSERT, UPDATE, DELETE)
            table: Table name being accessed
            tenant_id: Optional tenant ID for context
        """
        self.operation = operation
        self.table = table
        self.tenant_id = tenant_id
        self.span = None
        self.start_time = None

    def __enter__(self):
        """Enter the tracing context."""
        self.start_time = time.time()
        attributes = {
            "db.operation": self.operation,
            "db.table": self.table,
            "db.system": "postgresql",
        }
        if self.tenant_id:
            attributes["tenant.id"] = self.tenant_id

        self.span = create_span(
            f"DB {self.operation} {self.table}",
            kind=SpanKind.CLIENT,
            attributes=attributes,
            tenant_id=self.tenant_id,
        )
        return self.span.__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the tracing context."""
        if self.span:
            duration_ms = (time.time() - self.start_time) * 1000
            add_span_attributes({"db.duration_ms": duration_ms})

            if exc_type:
                set_span_status(False, str(exc_val))
            else:
                set_span_status(True, "OK")

            return self.span.__exit__(exc_type, exc_val, exc_tb)


class StorageTracingMiddleware:
    """
    Context manager for tracing storage operations.

    Usage:
        with StorageTracingMiddleware("upload", "s3", tenant_id):
            await storage.upload(file)
    """

    def __init__(
        self,
        operation: str,
        provider: str,
        tenant_id: Optional[str] = None,
        bucket: Optional[str] = None,
    ):
        """
        Initialize storage tracing context.

        Args:
            operation: Storage operation (upload, download, delete, list)
            provider: Storage provider (s3, azure_blob, gcs)
            tenant_id: Optional tenant ID for context
            bucket: Optional bucket name
        """
        self.operation = operation
        self.provider = provider
        self.tenant_id = tenant_id
        self.bucket = bucket
        self.span = None
        self.start_time = None

    def __enter__(self):
        """Enter the tracing context."""
        self.start_time = time.time()
        attributes = {
            "storage.operation": self.operation,
            "storage.provider": self.provider,
        }
        if self.bucket:
            attributes["storage.bucket"] = self.bucket
        if self.tenant_id:
            attributes["tenant.id"] = self.tenant_id

        self.span = create_span(
            f"Storage {self.operation}",
            kind=SpanKind.CLIENT,
            attributes=attributes,
            tenant_id=self.tenant_id,
        )
        return self.span.__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the tracing context."""
        if self.span:
            duration_ms = (time.time() - self.start_time) * 1000
            add_span_attributes({"storage.duration_ms": duration_ms})

            if exc_type:
                set_span_status(False, str(exc_val))
            else:
                set_span_status(True, "OK")

            return self.span.__exit__(exc_type, exc_val, exc_tb)
