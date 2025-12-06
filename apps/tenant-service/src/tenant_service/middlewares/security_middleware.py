"""Security headers middleware for API protection.

This module provides:
- Standard security headers for all responses
- CORS hardening
- Content Security Policy
- Protection against common web vulnerabilities
"""

import logging
from dataclasses import dataclass, field
from typing import Callable, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


@dataclass
class SecurityHeadersConfig:
    """Configuration for security headers."""

    # Strict Transport Security
    hsts_enabled: bool = True
    hsts_max_age: int = 31536000  # 1 year
    hsts_include_subdomains: bool = True
    hsts_preload: bool = False

    # Content Security Policy
    csp_enabled: bool = True
    csp_default_src: str = "'self'"
    csp_script_src: str = "'self'"
    csp_style_src: str = "'self' 'unsafe-inline'"  # Allow inline styles for Swagger UI
    csp_img_src: str = "'self' data:"
    csp_connect_src: str = "'self'"
    csp_frame_ancestors: str = "'none'"

    # Other security headers
    x_content_type_options: str = "nosniff"
    x_frame_options: str = "DENY"
    x_xss_protection: str = "1; mode=block"
    referrer_policy: str = "strict-origin-when-cross-origin"
    permissions_policy: str = "geolocation=(), microphone=(), camera=()"

    # Cache control
    cache_control: str = "no-store, no-cache, must-revalidate, proxy-revalidate"
    pragma: str = "no-cache"

    # Paths to exclude from certain headers (e.g., docs)
    excluded_paths: list[str] = field(default_factory=lambda: ["/docs", "/redoc", "/openapi.json"])


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for adding security headers.

    Features:
    - HTTP Strict Transport Security (HSTS)
    - Content Security Policy (CSP)
    - X-Content-Type-Options
    - X-Frame-Options
    - X-XSS-Protection
    - Referrer Policy
    - Permissions Policy
    - Cache Control for sensitive endpoints
    """

    def __init__(
        self,
        app: ASGIApp,
        config: Optional[SecurityHeadersConfig] = None,
    ):
        """
        Initialize security headers middleware.

        Args:
            app: ASGI application
            config: Security headers configuration
        """
        super().__init__(app)
        self.config = config or SecurityHeadersConfig()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and add security headers.

        Args:
            request: Incoming FastAPI request
            call_next: Next middleware/handler

        Returns:
            Response with security headers
        """
        response = await call_next(request)

        # Determine if this is a documentation path
        is_docs_path = request.url.path in self.config.excluded_paths

        # Add security headers
        self._add_security_headers(response, is_docs_path)

        return response

    def _add_security_headers(self, response: Response, is_docs_path: bool) -> None:
        """
        Add security headers to the response.

        Args:
            response: Response to modify
            is_docs_path: Whether this is a documentation path
        """
        # HSTS - Only add for HTTPS connections (or always in production)
        if self.config.hsts_enabled:
            hsts_value = f"max-age={self.config.hsts_max_age}"
            if self.config.hsts_include_subdomains:
                hsts_value += "; includeSubDomains"
            if self.config.hsts_preload:
                hsts_value += "; preload"
            response.headers["Strict-Transport-Security"] = hsts_value

        # Content Security Policy - relaxed for docs
        if self.config.csp_enabled and not is_docs_path:
            csp_parts = [
                f"default-src {self.config.csp_default_src}",
                f"script-src {self.config.csp_script_src}",
                f"style-src {self.config.csp_style_src}",
                f"img-src {self.config.csp_img_src}",
                f"connect-src {self.config.csp_connect_src}",
                f"frame-ancestors {self.config.csp_frame_ancestors}",
            ]
            response.headers["Content-Security-Policy"] = "; ".join(csp_parts)

        # Standard security headers
        response.headers["X-Content-Type-Options"] = self.config.x_content_type_options
        response.headers["X-Frame-Options"] = self.config.x_frame_options
        response.headers["X-XSS-Protection"] = self.config.x_xss_protection
        response.headers["Referrer-Policy"] = self.config.referrer_policy
        response.headers["Permissions-Policy"] = self.config.permissions_policy

        # Cache control for non-static responses
        if not is_docs_path:
            response.headers["Cache-Control"] = self.config.cache_control
            response.headers["Pragma"] = self.config.pragma


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """
    Middleware for validating and sanitizing incoming requests.

    Features:
    - Content-Type validation
    - Request size limits
    - Header validation
    - Path traversal prevention
    """

    def __init__(
        self,
        app: ASGIApp,
        max_content_length: int = 10 * 1024 * 1024,  # 10 MB
        allowed_content_types: Optional[list[str]] = None,
    ):
        """
        Initialize request validation middleware.

        Args:
            app: ASGI application
            max_content_length: Maximum request body size in bytes
            allowed_content_types: Allowed Content-Type headers
        """
        super().__init__(app)
        self.max_content_length = max_content_length
        self.allowed_content_types = allowed_content_types or [
            "application/json",
            "application/x-www-form-urlencoded",
            "multipart/form-data",
        ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Validate request and process.

        Args:
            request: Incoming FastAPI request
            call_next: Next middleware/handler

        Returns:
            Response or error if validation fails
        """
        # Check content length
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_content_length:
            from fastapi.responses import JSONResponse
            from fastapi import status

            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={
                    "error_code": "REQUEST_TOO_LARGE",
                    "message": f"Request body exceeds maximum size of {self.max_content_length} bytes",
                },
            )

        # Validate Content-Type for POST/PUT/PATCH requests
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "")
            content_type_base = content_type.split(";")[0].strip().lower()

            if content_type_base and content_type_base not in self.allowed_content_types:
                from fastapi.responses import JSONResponse
                from fastapi import status

                return JSONResponse(
                    status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                    content={
                        "error_code": "UNSUPPORTED_MEDIA_TYPE",
                        "message": f"Content-Type '{content_type_base}' is not supported",
                        "details": {
                            "allowed_types": self.allowed_content_types,
                        },
                    },
                )

        # Check for path traversal attempts
        if ".." in request.url.path or "//" in request.url.path:
            from fastapi.responses import JSONResponse
            from fastapi import status

            logger.warning(f"Path traversal attempt detected: {request.url.path}")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "error_code": "INVALID_PATH",
                    "message": "Invalid request path",
                },
            )

        return await call_next(request)


def get_security_headers_for_environment(environment: str = "production") -> SecurityHeadersConfig:
    """
    Get security headers configuration based on environment.

    Args:
        environment: Deployment environment (development, staging, production)

    Returns:
        SecurityHeadersConfig appropriate for the environment
    """
    if environment == "development":
        return SecurityHeadersConfig(
            hsts_enabled=False,
            csp_enabled=False,
            cache_control="no-cache",
        )
    elif environment == "staging":
        return SecurityHeadersConfig(
            hsts_max_age=86400,  # 1 day
            hsts_preload=False,
        )
    else:  # production
        return SecurityHeadersConfig(
            hsts_max_age=31536000,  # 1 year
            hsts_preload=True,
            hsts_include_subdomains=True,
        )
