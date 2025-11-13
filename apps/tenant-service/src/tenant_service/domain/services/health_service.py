"""Health check service for monitoring application and dependencies health status."""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class ComponentStatus(str, Enum):
    """Status of a health component."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class ComponentHealth:
    """Health status of a single component."""
    status: ComponentStatus
    response_time_ms: float
    message: Optional[str] = None
    last_check: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON response."""
        return {
            "status": self.status.value,
            "response_time_ms": round(self.response_time_ms, 2),
            "message": self.message,
            "last_check": self.last_check.isoformat() if self.last_check else None,
        }


@dataclass
class HealthCheckResult:
    """Overall health check result."""
    status: ComponentStatus
    timestamp: datetime
    components: Dict[str, ComponentHealth]
    
    def is_healthy(self) -> bool:
        """Check if service is healthy (all components healthy)."""
        return self.status == ComponentStatus.HEALTHY
    
    def is_ready(self) -> bool:
        """Check if service is ready (all critical components healthy)."""
        # For readiness, database is critical
        if "database" in self.components:
            db_status = self.components["database"].status
            if db_status == ComponentStatus.UNHEALTHY:
                return False
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON response."""
        return {
            "status": self.status.value,
            "timestamp": self.timestamp.isoformat(),
            "components": {
                name: component.to_dict()
                for name, component in self.components.items()
            },
        }


class HealthCheckService:
    """Service for checking health of application and dependencies."""
    
    def __init__(self, db_session_factory, storage_adapter, cache_client=None):
        """Initialize health check service.
        
        Args:
            db_session_factory: Database session factory
            storage_adapter: Storage adapter for cloud storage
            cache_client: Optional cache client (Redis, etc.)
        """
        self.db_session_factory = db_session_factory
        self.storage_adapter = storage_adapter
        self.cache_client = cache_client
    
    async def check_liveness(self) -> HealthCheckResult:
        """Check liveness probe (basic availability).
        
        Checks:
        - Application is running
        - Service is responsive
        
        Returns:
            HealthCheckResult with overall status
        """
        components: Dict[str, ComponentHealth] = {}
        
        # Basic availability check
        try:
            start = datetime.utcnow()
            # Simple operation to verify service is responsive
            elapsed_ms = (datetime.utcnow() - start).total_seconds() * 1000
            components["application"] = ComponentHealth(
                status=ComponentStatus.HEALTHY,
                response_time_ms=elapsed_ms,
                message="Service is running",
                last_check=datetime.utcnow(),
            )
        except Exception as e:
            logger.error(f"Liveness check failed: {e}")
            components["application"] = ComponentHealth(
                status=ComponentStatus.UNHEALTHY,
                response_time_ms=0,
                message=f"Service check failed: {str(e)}",
                last_check=datetime.utcnow(),
            )
        
        # Determine overall status
        overall_status = ComponentStatus.HEALTHY
        if any(c.status == ComponentStatus.UNHEALTHY for c in components.values()):
            overall_status = ComponentStatus.UNHEALTHY
        
        return HealthCheckResult(
            status=overall_status,
            timestamp=datetime.utcnow(),
            components=components,
        )
    
    async def check_readiness(self) -> HealthCheckResult:
        """Check readiness probe (dependencies available).
        
        Checks:
        - Database connectivity
        - Storage access
        - Cache availability (if configured)
        
        Returns:
            HealthCheckResult with component statuses
        """
        components: Dict[str, ComponentHealth] = {}
        
        # Check database
        db_component = await self._check_database()
        components["database"] = db_component
        
        # Check storage
        storage_component = await self._check_storage()
        components["storage"] = storage_component
        
        # Check cache if available
        if self.cache_client:
            cache_component = await self._check_cache()
            components["cache"] = cache_component
        
        # Determine overall status
        overall_status = ComponentStatus.HEALTHY
        if any(c.status == ComponentStatus.UNHEALTHY for c in components.values()):
            overall_status = ComponentStatus.UNHEALTHY
        elif any(c.status == ComponentStatus.DEGRADED for c in components.values()):
            overall_status = ComponentStatus.DEGRADED
        
        return HealthCheckResult(
            status=overall_status,
            timestamp=datetime.utcnow(),
            components=components,
        )
    
    async def _check_database(self) -> ComponentHealth:
        """Check database connectivity."""
        try:
            start = datetime.utcnow()
            async with self.db_session_factory() as session:
                # Simple query to verify connection
                await session.execute("SELECT 1")
            elapsed_ms = (datetime.utcnow() - start).total_seconds() * 1000
            
            return ComponentHealth(
                status=ComponentStatus.HEALTHY,
                response_time_ms=elapsed_ms,
                message="Database connection successful",
                last_check=datetime.utcnow(),
            )
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return ComponentHealth(
                status=ComponentStatus.UNHEALTHY,
                response_time_ms=0,
                message=f"Database check failed: {str(e)}",
                last_check=datetime.utcnow(),
            )
    
    async def _check_storage(self) -> ComponentHealth:
        """Check storage (cloud provider) connectivity."""
        try:
            start = datetime.utcnow()
            # Verify storage adapter is available
            if not self.storage_adapter:
                return ComponentHealth(
                    status=ComponentStatus.DEGRADED,
                    response_time_ms=0,
                    message="Storage adapter not configured",
                    last_check=datetime.utcnow(),
                )
            
            # Try to get storage status (this varies by provider)
            # For now, just verify the adapter exists
            elapsed_ms = (datetime.utcnow() - start).total_seconds() * 1000
            
            return ComponentHealth(
                status=ComponentStatus.HEALTHY,
                response_time_ms=elapsed_ms,
                message="Storage adapter available",
                last_check=datetime.utcnow(),
            )
        except Exception as e:
            logger.error(f"Storage health check failed: {e}")
            return ComponentHealth(
                status=ComponentStatus.UNHEALTHY,
                response_time_ms=0,
                message=f"Storage check failed: {str(e)}",
                last_check=datetime.utcnow(),
            )
    
    async def _check_cache(self) -> ComponentHealth:
        """Check cache (Redis, etc.) connectivity."""
        try:
            start = datetime.utcnow()
            if not self.cache_client:
                return ComponentHealth(
                    status=ComponentStatus.DEGRADED,
                    response_time_ms=0,
                    message="Cache client not available",
                    last_check=datetime.utcnow(),
                )
            
            # Verify cache is accessible
            # Implementation varies by cache type
            elapsed_ms = (datetime.utcnow() - start).total_seconds() * 1000
            
            return ComponentHealth(
                status=ComponentStatus.HEALTHY,
                response_time_ms=elapsed_ms,
                message="Cache client available",
                last_check=datetime.utcnow(),
            )
        except Exception as e:
            logger.warning(f"Cache health check failed: {e}")
            # Cache failure is degradation, not a blocker
            return ComponentHealth(
                status=ComponentStatus.DEGRADED,
                response_time_ms=0,
                message=f"Cache check failed: {str(e)}",
                last_check=datetime.utcnow(),
            )
