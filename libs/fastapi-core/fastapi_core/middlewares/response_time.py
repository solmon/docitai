import time
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from fastapi_core._build_info import BUILD_TIME
from fastapi_core._version import __version__
from fastapi_core.config import get_logger


logger = get_logger(__name__)


class ResponseTimeMiddleware(BaseHTTPMiddleware):
    """
    Middleware to measure and include the response time in the HTTP headers.

    This middleware calculates the time taken to process a request and adds it to the response headers
    as `x-response-time` in milliseconds.

    Attributes
    ----------
        None

    """

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        """
        Measures the time taken to process a request and adds the response time to the headers.

        Args:
        ----
            request (Request): The incoming HTTP request object.
            call_next (Callable): A function to process the request and return a response.

        Returns:
        -------
            response (Response): The HTTP response object with the response time header added.

        """
        # Record the start time before processing the request
        start_time = time.time()

        await log_request(request)

        # Call the next middleware or endpoint handler
        response = await call_next(request)

        # Calculate the time taken to process the request
        process_time = time.time() - start_time

        # Add the response time to the response headers in milliseconds
        response.headers["x-response-time"] = f"{process_time * 1000:.3f}ms"

        # Add server name based on version and build time
        response.headers["x-server-name"] = f"{__version__}/{BUILD_TIME}"

        await log_response(request, response, process_time)

        return response


async def log_request(request: Request) -> None:
    client = request.client  # This can be None
    req = {
        "method": request.method,
        "url": str(request.url.path),
        "remoteAddress": client.host if client else "unknown",
        "remotePort": client.port if client else "unknown",
    }
    logger.info("REQUEST", req=req)


async def log_response(request: Request, response: Response, response_time: float) -> None:
    res = {
        "url": request.url.path,
        "status_code": response.status_code,
        "response_time": response_time,
    }
    logger.info("RESPONSE", res=res)
