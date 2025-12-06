"""Health check endpoints for Kubernetes probes and monitoring."""

from fastapi import APIRouter, Depends
from typing import Dict, Any
import logging

from tenant_service.domain.services.health_service import (
    HealthCheckService,
    ComponentStatus,
)
from tenant_service.api.dependencies import get_db_session as get_async_session

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="",
    tags=["health"],
)


def get_health_service(session=Depends(get_async_session)) -> HealthCheckService:
    """Get health check service with dependencies.

    Args:
        session: Database session

    Returns:
        HealthCheckService instance
    """
    # TODO: Inject storage_adapter and cache_client from app context
    return HealthCheckService(
        db_session_factory=get_async_session,
        storage_adapter=None,  # Will be set from app context
        cache_client=None,  # Will be set from app context
    )


@router.get(
    "/health",
    response_model=Dict[str, Any],
    status_code=200,
    responses={
        200: {"description": "Service is healthy and ready"},
        503: {"description": "Service is unhealthy"},
    },
    summary="Liveness Probe",
    description="Kubernetes liveness probe - checks if service is running. Used to determine if pod should be restarted.",
)
async def liveness_probe(
    health_service: HealthCheckService = Depends(get_health_service),
) -> Dict[str, Any]:
    """Liveness probe endpoint.

    This endpoint is used by Kubernetes to check if the pod is running.
    A failed probe will result in pod restart.

    Returns:
        Health status and component details
    """
    try:
        result = await health_service.check_liveness()

        return {
            "status": result.status.value,
            "timestamp": result.timestamp.isoformat(),
            "components": {name: component.to_dict() for name, component in result.components.items()},
        }
    except Exception as e:
        logger.error(f"Liveness probe failed: {e}", exc_info=True)
        return {
            "status": ComponentStatus.UNHEALTHY.value,
            "timestamp": None,
            "error": "Failed to check liveness",
        }


@router.get(
    "/health/ready",
    response_model=Dict[str, Any],
    status_code=200,
    responses={
        200: {"description": "Service is ready to handle traffic"},
        503: {"description": "Service dependencies are unavailable"},
    },
    summary="Readiness Probe",
    description="Kubernetes readiness probe - checks if all dependencies are available. Used to determine if pod should receive traffic.",
)
async def readiness_probe(
    health_service: HealthCheckService = Depends(get_health_service),
) -> Dict[str, Any]:
    """Readiness probe endpoint.

    This endpoint is used by Kubernetes to check if the pod is ready to receive traffic.
    A failed probe will result in traffic being routed away from the pod.

    Returns:
        Health status of all dependencies
    """
    try:
        result = await health_service.check_readiness()

        # For readiness, we need all critical components healthy

        return {
            "status": result.status.value,
            "timestamp": result.timestamp.isoformat(),
            "ready": result.is_ready(),
            "components": {name: component.to_dict() for name, component in result.components.items()},
        }
    except Exception as e:
        logger.error(f"Readiness probe failed: {e}", exc_info=True)
        return {
            "status": ComponentStatus.UNHEALTHY.value,
            "timestamp": None,
            "ready": False,
            "error": "Failed to check readiness",
        }


@router.get(
    "/health/detailed",
    response_model=Dict[str, Any],
    status_code=200,
    summary="Detailed Health Status",
    description="Detailed health check with response times and component details.",
)
async def detailed_health(
    health_service: HealthCheckService = Depends(get_health_service),
) -> Dict[str, Any]:
    """Detailed health status endpoint.

    Provides comprehensive health information including response times
    and detailed component status. Useful for monitoring dashboards.

    Returns:
        Detailed health status for all components
    """
    try:
        liveness = await health_service.check_liveness()
        readiness = await health_service.check_readiness()

        return {
            "liveness": {
                "status": liveness.status.value,
                "timestamp": liveness.timestamp.isoformat(),
                "components": {name: component.to_dict() for name, component in liveness.components.items()},
            },
            "readiness": {
                "status": readiness.status.value,
                "timestamp": readiness.timestamp.isoformat(),
                "ready": readiness.is_ready(),
                "components": {name: component.to_dict() for name, component in readiness.components.items()},
            },
        }
    except Exception as e:
        logger.error(f"Detailed health check failed: {e}", exc_info=True)
        return {
            "error": "Failed to check detailed health",
            "message": str(e),
        }
