from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce security headers and Content Security Policy (CSP) for FastAPI applications.

    This middleware sets various security-related HTTP headers to enhance the security of the application.
    It applies a default Content Security Policy (CSP) to all routes except those starting with '/openapi'
    or '/redoc', which have specific CSPs tailored for Swagger UI and ReDoc documentation.

    Attributes
    ----------
        csp_default (str): Default Content Security Policy applied to all paths not matching specific rules.

    """

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        """
        Processes the incoming request, applies the security headers, and returns the response.

        Args:
        ----
            request (Request): The incoming HTTP request object.
            call_next (Callable): A function to process the request and return a response.

        Returns:
        -------
            response (Response): The HTTP response object with security headers applied.

        """
        # Call the next middleware or endpoint handler
        response = await call_next(request)

        # Default CSP for paths other than '/openapi' and '/redoc'
        csp_default = "default-src 'self';"

        # Determine the CSP based on the request path
        if request.url.path.startswith("/openapi"):
            # Specific CSP for Swagger UI paths
            csp = (
                "default-src 'self'; "
                "style-src 'self' https://cdn.jsdelivr.net; "
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "img-src 'self' data: https://fastapi.tiangolo.com; "
                "connect-src 'self'; "
                "frame-src 'self'; "
                "frame-ancestors 'self'; "
                "base-uri 'self';"
            )
        elif request.url.path.startswith("/redoc"):
            # Specific CSP for ReDoc documentation paths
            csp = (
                "default-src 'self'; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "script-src 'self' https://cdn.jsdelivr.net; "
                "font-src 'self' https://fonts.googleapis.com https://fonts.gstatic.com; "
                "img-src 'self' data: https://fastapi.tiangolo.com https://cdn.redoc.ly; "
                "connect-src 'self'; "
                "worker-src 'self' blob:; "  # Allow workers from blob URLs
                "frame-src 'self'; "
                "frame-ancestors 'self'; "
                "base-uri 'self';"
            )
        else:
            # Apply default CSP for other paths
            csp = csp_default

        # Apply security headers to the response
        response.headers["Content-Security-Policy"] = csp  # Apply the determined CSP to the response
        response.headers["Cross-Origin-Opener-Policy"] = (
            "same-origin"  # Restrict the ability of cross-origin documents to interact with the page
        )
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"  # Restrict cross-origin resource sharing
        response.headers["Origin-Agent-Cluster"] = "?1"  # Enable origin-agent-cluster
        response.headers["Referrer-Policy"] = "no-referrer"  # Do not send referrer information
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"  # Enforce HTTPS for future requests
        )
        response.headers["X-Content-Type-Options"] = "nosniff"  # Prevent MIME type sniffing
        response.headers["X-DNS-Prefetch-Control"] = "off"  # Disable DNS prefetching
        response.headers["X-Download-Options"] = "noopen"  # Prevent downloads from being opened automatically
        response.headers["X-Frame-Options"] = "DENY"  # Prevent the page from being displayed in frames
        response.headers["X-Permitted-Cross-Domain-Policies"] = (
            "none"  # Prevent Adobe Flash and Acrobat from accessing the domain
        )
        response.headers["X-XSS-Protection"] = "1; mode=block"  # Enable cross-site scripting filter

        return response
