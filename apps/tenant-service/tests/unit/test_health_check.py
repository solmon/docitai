"""Health check endpoint tests."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, Mock
from datetime import datetime

from tenant_service.main import app
from tenant_service.domain.services.health_service import (
    ComponentStatus,
    ComponentHealth,
    HealthCheckResult,
    HealthCheckService,
)


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


class TestHealthCheckService:
    """Tests for HealthCheckService."""

    @pytest.mark.asyncio
    async def test_check_liveness_healthy(self):
        """Test liveness check when service is healthy."""
        service = HealthCheckService(
            db_session_factory=AsyncMock(),
            storage_adapter=Mock(),
        )

        result = await service.check_liveness()

        assert result.is_healthy()
        assert result.status == ComponentStatus.HEALTHY
        assert "application" in result.components
        assert result.components["application"].status == ComponentStatus.HEALTHY

    @pytest.mark.asyncio
    async def test_check_readiness_healthy(self):
        """Test readiness check when all dependencies are available."""
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock()

        service = HealthCheckService(
            db_session_factory=mock_session,
            storage_adapter=Mock(),
        )

        result = await service.check_readiness()

        assert result.is_ready()
        assert "database" in result.components
        assert "storage" in result.components

    @pytest.mark.asyncio
    async def test_check_readiness_degraded_with_cache(self):
        """Test readiness check with degraded cache."""
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock()

        mock_cache = AsyncMock()
        mock_cache.ping = AsyncMock(side_effect=Exception("Connection failed"))

        service = HealthCheckService(
            db_session_factory=mock_session,
            storage_adapter=Mock(),
            cache_client=mock_cache,
        )

        result = await service.check_readiness()

        # Should still be ready (database is critical, cache is not)
        assert result.is_ready()
        assert result.components["cache"].status == ComponentStatus.DEGRADED

    @pytest.mark.asyncio
    async def test_check_readiness_unhealthy_database(self):
        """Test readiness check when database is unavailable."""
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(side_effect=Exception("Database connection failed"))

        service = HealthCheckService(
            db_session_factory=mock_session,
            storage_adapter=Mock(),
        )

        result = await service.check_readiness()

        assert not result.is_ready()
        assert result.components["database"].status == ComponentStatus.UNHEALTHY


class TestHealthCheckEndpoints:
    """Tests for health check API endpoints."""

    def test_liveness_probe_healthy(self, client):
        """Test GET /health returns 200 when healthy."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == ComponentStatus.HEALTHY.value
        assert "timestamp" in data
        assert "components" in data

    def test_readiness_probe_structure(self, client):
        """Test GET /health/ready returns proper structure."""
        response = client.get("/health/ready")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] in [
            ComponentStatus.HEALTHY.value,
            ComponentStatus.DEGRADED.value,
            ComponentStatus.UNHEALTHY.value,
        ]
        assert "ready" in data
        assert isinstance(data["ready"], bool)
        assert "components" in data

    def test_detailed_health_endpoint(self, client):
        """Test GET /health/detailed returns comprehensive status."""
        response = client.get("/health/detailed")

        assert response.status_code == 200
        data = response.json()
        assert "liveness" in data
        assert "readiness" in data
        assert data["liveness"]["status"] in [
            ComponentStatus.HEALTHY.value,
            ComponentStatus.DEGRADED.value,
            ComponentStatus.UNHEALTHY.value,
        ]
        assert data["readiness"]["status"] in [
            ComponentStatus.HEALTHY.value,
            ComponentStatus.DEGRADED.value,
            ComponentStatus.UNHEALTHY.value,
        ]

    def test_health_endpoints_no_authentication(self, client):
        """Test health endpoints don't require authentication."""
        # Health endpoints should be publicly accessible for Kubernetes probes
        response1 = client.get("/health")
        response2 = client.get("/health/ready")
        response3 = client.get("/health/detailed")

        # All should succeed (no 401 Unauthorized)
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response3.status_code == 200


class TestComponentHealth:
    """Tests for ComponentHealth model."""

    def test_component_health_to_dict(self):
        """Test ComponentHealth serialization."""
        component = ComponentHealth(
            status=ComponentStatus.HEALTHY,
            response_time_ms=25.5,
            message="All good",
            last_check=datetime(2025, 11, 13, 12, 0, 0),
        )

        result = component.to_dict()

        assert result["status"] == "healthy"
        assert result["response_time_ms"] == 25.5
        assert result["message"] == "All good"
        assert "last_check" in result

    def test_component_health_degraded(self):
        """Test ComponentHealth with degraded status."""
        component = ComponentHealth(
            status=ComponentStatus.DEGRADED,
            response_time_ms=500.0,
            message="Slow response",
        )

        result = component.to_dict()

        assert result["status"] == "degraded"
        assert result["response_time_ms"] == 500.0


class TestHealthCheckResult:
    """Tests for HealthCheckResult model."""

    def test_health_check_result_healthy(self):
        """Test healthy health check result."""
        components = {
            "database": ComponentHealth(
                status=ComponentStatus.HEALTHY,
                response_time_ms=10.0,
            ),
            "application": ComponentHealth(
                status=ComponentStatus.HEALTHY,
                response_time_ms=5.0,
            ),
        }
        result = HealthCheckResult(
            status=ComponentStatus.HEALTHY,
            timestamp=datetime.utcnow(),
            components=components,
        )

        assert result.is_healthy()
        assert result.is_ready()

    def test_health_check_result_unhealthy(self):
        """Test unhealthy health check result."""
        components = {
            "database": ComponentHealth(
                status=ComponentStatus.UNHEALTHY,
                response_time_ms=0.0,
                message="Connection failed",
            ),
        }
        result = HealthCheckResult(
            status=ComponentStatus.UNHEALTHY,
            timestamp=datetime.utcnow(),
            components=components,
        )

        assert not result.is_healthy()
        assert not result.is_ready()

    def test_health_check_result_degraded(self):
        """Test degraded health check result."""
        components = {
            "database": ComponentHealth(
                status=ComponentStatus.HEALTHY,
                response_time_ms=15.0,
            ),
            "cache": ComponentHealth(
                status=ComponentStatus.DEGRADED,
                response_time_ms=0.0,
                message="Slow response",
            ),
        }
        result = HealthCheckResult(
            status=ComponentStatus.DEGRADED,
            timestamp=datetime.utcnow(),
            components=components,
        )

        assert not result.is_healthy()
        assert result.is_ready()  # Cache not required for readiness

    def test_health_check_result_to_dict(self):
        """Test health check result serialization."""
        components = {
            "database": ComponentHealth(
                status=ComponentStatus.HEALTHY,
                response_time_ms=12.5,
                message="Connected",
                last_check=datetime(2025, 11, 13, 12, 0, 0),
            ),
        }
        result = HealthCheckResult(
            status=ComponentStatus.HEALTHY,
            timestamp=datetime(2025, 11, 13, 12, 0, 5),
            components=components,
        )

        result_dict = result.to_dict()

        assert result_dict["status"] == "healthy"
        assert "timestamp" in result_dict
        assert "components" in result_dict
        assert "database" in result_dict["components"]


# Integration tests
class TestHealthCheckIntegration:
    """Integration tests for health checks."""

    def test_liveness_ready_readiness_flow(self, client):
        """Test typical Kubernetes probe flow."""
        # Initial liveness check
        liveness = client.get("/health")
        assert liveness.status_code == 200

        # Application is live, check readiness
        readiness = client.get("/health/ready")
        assert readiness.status_code == 200

        # If ready, get detailed status
        if readiness.json()["ready"]:
            detailed = client.get("/health/detailed")
            assert detailed.status_code == 200
            assert detailed.json()["readiness"]["ready"]

    def test_health_response_times(self, client):
        """Test health check endpoints respond quickly."""
        import time

        start = time.time()
        response = client.get("/health")
        elapsed = (time.time() - start) * 1000  # Convert to ms

        assert response.status_code == 200
        assert elapsed < 100, f"Health check took {elapsed}ms (expected <100ms)"

    def test_health_includes_response_times(self, client):
        """Test health response includes component response times."""
        response = client.get("/health/detailed")
        data = response.json()

        # Check that response times are included
        for component_name, component_data in data["readiness"]["components"].items():
            assert "response_time_ms" in component_data
            assert component_data["response_time_ms"] >= 0
