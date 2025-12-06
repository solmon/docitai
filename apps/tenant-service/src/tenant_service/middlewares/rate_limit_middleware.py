"""Rate limiting middleware for tenant-aware API protection.

This module provides:
- Per-tenant rate limiting with configurable limits
- Sliding window algorithm for accurate rate limiting
- Different limits for authenticated vs anonymous requests
- Rate limit headers in responses
"""

import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Dict, Optional

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""

    # Requests per window for anonymous users
    anonymous_limit: int = 100
    anonymous_window_seconds: int = 60

    # Requests per window for authenticated users
    authenticated_limit: int = 1000
    authenticated_window_seconds: int = 60

    # Per-tenant limits (can override authenticated limits)
    tenant_limits: Dict[str, int] = field(default_factory=dict)

    # Paths excluded from rate limiting
    excluded_paths: list[str] = field(
        default_factory=lambda: ["/health", "/health/ready", "/health/detailed", "/metrics", "/docs", "/openapi.json"]
    )


@dataclass
class RateLimitWindow:
    """Sliding window rate limit tracker."""

    requests: list[float] = field(default_factory=list)
    window_seconds: int = 60
    limit: int = 100

    def add_request(self) -> bool:
        """
        Add a request to the window.

        Returns:
            True if request is allowed, False if rate limited
        """
        current_time = time.time()
        cutoff_time = current_time - self.window_seconds

        # Remove old requests outside the window
        self.requests = [ts for ts in self.requests if ts > cutoff_time]

        # Check if we're over the limit
        if len(self.requests) >= self.limit:
            return False

        # Add new request
        self.requests.append(current_time)
        return True

    def get_remaining(self) -> int:
        """Get remaining requests in current window."""
        current_time = time.time()
        cutoff_time = current_time - self.window_seconds
        current_requests = len([ts for ts in self.requests if ts > cutoff_time])
        return max(0, self.limit - current_requests)

    def get_reset_time(self) -> int:
        """Get seconds until the window resets."""
        if not self.requests:
            return self.window_seconds

        oldest_request = min(self.requests)
        reset_time = oldest_request + self.window_seconds - time.time()
        return max(0, int(reset_time))


class RateLimiter:
    """
    Rate limiter with per-client and per-tenant tracking.

    Uses sliding window algorithm for accurate rate limiting.
    """

    def __init__(self, config: Optional[RateLimitConfig] = None):
        """
        Initialize rate limiter.

        Args:
            config: Rate limiting configuration
        """
        self.config = config or RateLimitConfig()
        self._windows: Dict[str, RateLimitWindow] = defaultdict(
            lambda: RateLimitWindow(
                window_seconds=self.config.anonymous_window_seconds,
                limit=self.config.anonymous_limit,
            )
        )

    def check_rate_limit(
        self,
        client_key: str,
        tenant_id: Optional[str] = None,
        is_authenticated: bool = False,
    ) -> tuple[bool, int, int]:
        """
        Check if a request is rate limited.

        Args:
            client_key: Unique identifier for the client (IP or user ID)
            tenant_id: Optional tenant ID for tenant-specific limits
            is_authenticated: Whether the request is authenticated

        Returns:
            Tuple of (is_allowed, remaining_requests, reset_time_seconds)
        """
        # Determine the limit and window for this request
        if tenant_id and tenant_id in self.config.tenant_limits:
            limit = self.config.tenant_limits[tenant_id]
            window_seconds = self.config.authenticated_window_seconds
        elif is_authenticated:
            limit = self.config.authenticated_limit
            window_seconds = self.config.authenticated_window_seconds
        else:
            limit = self.config.anonymous_limit
            window_seconds = self.config.anonymous_window_seconds

        # Build the key for tracking
        tracking_key = f"{client_key}:{tenant_id or 'anonymous'}"

        # Get or create window for this key
        if tracking_key not in self._windows:
            self._windows[tracking_key] = RateLimitWindow(
                window_seconds=window_seconds,
                limit=limit,
            )
        else:
            # Update limits if they changed
            self._windows[tracking_key].limit = limit
            self._windows[tracking_key].window_seconds = window_seconds

        window = self._windows[tracking_key]

        # Check and add request
        is_allowed = window.add_request()
        remaining = window.get_remaining()
        reset_time = window.get_reset_time()

        return is_allowed, remaining, reset_time

    def cleanup_expired_windows(self) -> int:
        """
        Remove expired windows to prevent memory growth.

        Returns:
            Number of windows cleaned up
        """
        current_time = time.time()
        expired_keys = []

        for key, window in self._windows.items():
            if not window.requests:
                expired_keys.append(key)
            elif max(window.requests) < current_time - window.window_seconds * 2:
                expired_keys.append(key)

        for key in expired_keys:
            del self._windows[key]

        return len(expired_keys)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for rate limiting.

    Features:
    - Per-client rate limiting based on IP or user ID
    - Per-tenant rate limiting with configurable limits
    - Standard rate limit headers in responses
    - Graceful handling of rate limit errors
    """

    def __init__(
        self,
        app: ASGIApp,
        config: Optional[RateLimitConfig] = None,
    ):
        """
        Initialize rate limiting middleware.

        Args:
            app: ASGI application
            config: Rate limiting configuration
        """
        super().__init__(app)
        self.config = config or RateLimitConfig()
        self.limiter = RateLimiter(self.config)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with rate limiting.

        Args:
            request: Incoming FastAPI request
            call_next: Next middleware/handler

        Returns:
            Response with rate limit headers
        """
        # Skip rate limiting for excluded paths
        if request.url.path in self.config.excluded_paths:
            return await call_next(request)

        # Get client identifier
        client_key = self._get_client_key(request)

        # Extract tenant and auth info
        tenant_id = self._extract_tenant_id(request)
        is_authenticated = self._is_authenticated(request)

        # Check rate limit
        is_allowed, remaining, reset_time = self.limiter.check_rate_limit(
            client_key=client_key,
            tenant_id=tenant_id,
            is_authenticated=is_authenticated,
        )

        if not is_allowed:
            logger.warning(
                f"Rate limit exceeded for client {client_key}, tenant {tenant_id}",
                extra={"client_key": client_key, "tenant_id": tenant_id},
            )
            return self._rate_limit_response(remaining, reset_time)

        # Process request and add headers
        response = await call_next(request)

        # Add rate limit headers
        limit = (
            self.config.tenant_limits.get(tenant_id, self.config.authenticated_limit)
            if tenant_id
            else self.config.anonymous_limit
        )
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(time.time()) + reset_time)

        return response

    def _get_client_key(self, request: Request) -> str:
        """
        Get unique identifier for the client.

        Args:
            request: FastAPI request

        Returns:
            Client identifier string
        """
        # Try X-Forwarded-For for proxied requests
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        # Try X-Real-IP
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        # Fall back to direct client IP
        if request.client:
            return request.client.host

        return "unknown"

    def _extract_tenant_id(self, request: Request) -> Optional[str]:
        """Extract tenant ID from request."""
        # Try X-Tenant-ID header
        tenant_id = request.headers.get("x-tenant-id")
        if tenant_id:
            return tenant_id

        # Try to extract from path
        path_parts = request.url.path.split("/")
        try:
            if "tenants" in path_parts:
                tenant_index = path_parts.index("tenants") + 1
                if tenant_index < len(path_parts) and path_parts[tenant_index]:
                    return path_parts[tenant_index]
        except (ValueError, IndexError):
            pass

        return None

    def _is_authenticated(self, request: Request) -> bool:
        """Check if request has authentication."""
        auth_header = request.headers.get("authorization", "")
        return auth_header.startswith("Bearer ")

    def _rate_limit_response(self, remaining: int, reset_time: int) -> JSONResponse:
        """Create rate limit exceeded response."""
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error_code": "RATE_LIMIT_EXCEEDED",
                "message": "Too many requests. Please try again later.",
                "details": {
                    "retry_after_seconds": reset_time,
                },
            },
            headers={
                "X-RateLimit-Limit": "0",
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(time.time()) + reset_time),
                "Retry-After": str(reset_time),
            },
        )
