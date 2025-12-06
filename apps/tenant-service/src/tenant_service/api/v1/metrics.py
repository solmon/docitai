"""Prometheus metrics endpoint.

Note: Metrics endpoint is now provided by fastapi-core app_factory at /metrics
This module is kept for backward compatibility but is deprecated.
"""

from fastapi import APIRouter

router = APIRouter(
    prefix="",
    tags=["metrics"],
)

# Metrics endpoint is now provided by fastapi-core's create_app()
# at /metrics endpoint. This module is deprecated.
