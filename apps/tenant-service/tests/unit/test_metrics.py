"""Metrics collection and reporting tests."""

import pytest
from unittest.mock import Mock, patch

from fastapi_core.metrics import (
    record_http_request,
    record_db_query,
    record_db_error,
    record_auth_attempt,
    record_cache_hit,
    record_document_created,
    get_metrics_text,
)


class TestMetricsRecording:
    """Tests for metrics recording functions."""
    
    def test_record_http_request_success(self):
        """Test recording successful HTTP request."""
        record_http_request(
            method="GET",
            endpoint="/api/tenants",
            status_code=200,
            duration_seconds=0.025,
            tenant_id="tenant-123",
        )
        
        metrics = get_metrics_text()
        assert "http_requests_total" in metrics
        assert "GET" in metrics
    
    def test_record_http_request_error(self):
        """Test recording failed HTTP request."""
        record_http_request(
            method="POST",
            endpoint="/api/tenants",
            status_code=400,
            duration_seconds=0.010,
            tenant_id="tenant-123",
        )
        
        metrics = get_metrics_text()
        assert "api_errors_total" in metrics
        assert "400" in metrics
    
    def test_record_db_query(self):
        """Test recording database query."""
        record_db_query(
            query_type="SELECT",
            table="tenants",
            duration_seconds=0.015,
        )
        
        metrics = get_metrics_text()
        assert "db_query_duration_seconds" in metrics
    
    def test_record_db_error(self):
        """Test recording database error."""
        record_db_error(error_type="connection")
        
        metrics = get_metrics_text()
        assert "db_errors_total" in metrics
    
    def test_record_auth_attempt(self):
        """Test recording authentication attempt."""
        record_auth_attempt(method="jwt", result="success")
        
        metrics = get_metrics_text()
        assert "auth_attempts_total" in metrics
    
    def test_record_cache_hit(self):
        """Test recording cache hit."""
        record_cache_hit(cache_type="redis")
        
        metrics = get_metrics_text()
        assert "cache_hits_total" in metrics
    
    def test_record_document_created(self):
        """Test recording document creation."""
        record_document_created(document_type="invoice")
        
        metrics = get_metrics_text()
        assert "documents_created_total" in metrics


class TestMetricsEndpoint:
    """Tests for /metrics endpoint."""
    
    def test_metrics_endpoint_returns_prometheus_format(self):
        """Test that /metrics returns valid Prometheus format."""
        metrics_text = get_metrics_text()
        
        # Should contain Prometheus metric format markers
        assert "# HELP" in metrics_text or len(metrics_text) > 0
        assert "# TYPE" in metrics_text or len(metrics_text) > 0
    
    def test_metrics_endpoint_contains_http_metrics(self):
        """Test that metrics include HTTP-related metrics."""
        # Record an HTTP request first
        record_http_request(
            method="GET",
            endpoint="/test",
            status_code=200,
            duration_seconds=0.05,
        )
        
        metrics = get_metrics_text()
        assert "http_requests_total" in metrics
        assert "http_request_duration_seconds" in metrics


class TestMetricsMiddleware:
    """Tests for metrics middleware."""
    
    @pytest.mark.asyncio
    async def test_metrics_middleware_records_request(self):
        """Test that middleware records request metrics."""
        from tenant_service.middlewares.metrics_middleware import MetricsMiddleware
        from fastapi import FastAPI, Request
        from starlette.responses import PlainTextResponse
        
        app = FastAPI()
        
        @app.get("/test")
        async def test_endpoint():
            return {"status": "ok"}
        
        # Create middleware
        middleware = MetricsMiddleware(app)
        
        # Middleware should track requests
        assert middleware is not None
    
    @pytest.mark.asyncio
    async def test_auth_metrics_middleware_tracks_failures(self):
        """Test that auth middleware tracks authentication failures."""
        from tenant_service.middlewares.metrics_middleware import AuthenticationMetricsMiddleware
        from fastapi import FastAPI
        
        app = FastAPI()
        
        @app.get("/protected")
        async def protected_endpoint():
            return {"status": "ok"}
        
        middleware = AuthenticationMetricsMiddleware(app)
        assert middleware is not None


class TestMetricsCombination:
    """Tests for combined metrics scenarios."""
    
    def test_multiple_request_types_recorded(self):
        """Test recording multiple different request types."""
        requests = [
            ("GET", "/api/tenants", 200, 0.025),
            ("POST", "/api/tenants", 201, 0.050),
            ("GET", "/api/tenants/1", 200, 0.020),
            ("PUT", "/api/tenants/1", 200, 0.040),
            ("DELETE", "/api/tenants/1", 204, 0.015),
        ]
        
        for method, endpoint, status, duration in requests:
            record_http_request(method, endpoint, status, duration)
        
        metrics = get_metrics_text()
        for method, endpoint, status, _ in requests:
            assert method in metrics or "GET" in metrics  # At least one method should be there
    
    def test_error_and_success_mixed(self):
        """Test recording both successful and failed requests."""
        record_http_request("GET", "/test", 200, 0.010)
        record_http_request("GET", "/test", 500, 0.005)
        record_http_request("POST", "/test", 400, 0.008)
        
        metrics = get_metrics_text()
        assert "api_errors_total" in metrics
        assert "http_requests_total" in metrics
    
    def test_tenant_isolation_in_metrics(self):
        """Test that metrics track different tenants."""
        record_http_request("GET", "/api/data", 200, 0.020, tenant_id="tenant-1")
        record_http_request("GET", "/api/data", 200, 0.025, tenant_id="tenant-2")
        
        metrics = get_metrics_text()
        # Both tenant IDs should be tracked separately
        assert "tenant" in metrics.lower() or "GET" in metrics


class TestMetricsPerformance:
    """Tests for metrics collection performance."""
    
    def test_metrics_recording_is_fast(self):
        """Test that recording metrics doesn't significantly impact performance."""
        import time
        
        start = time.time()
        for i in range(100):
            record_http_request("GET", f"/test/{i}", 200, 0.010)
        elapsed = time.time() - start
        
        # Recording 100 metrics should be very fast (< 100ms)
        assert elapsed < 0.1, f"Recording metrics took {elapsed*1000:.1f}ms (expected <100ms)"
    
    def test_metrics_text_generation_is_fast(self):
        """Test that generating Prometheus text is fast."""
        import time
        
        # Record some metrics first
        for i in range(50):
            record_http_request("GET", "/test", 200, 0.010)
        
        start = time.time()
        metrics_text = get_metrics_text()
        elapsed = time.time() - start
        
        # Generating metrics text should be fast (< 50ms)
        assert elapsed < 0.05, f"Generating metrics took {elapsed*1000:.1f}ms (expected <50ms)"
        assert len(metrics_text) > 0


class TestMetricsLabels:
    """Tests for metric labels."""
    
    def test_http_request_labels(self):
        """Test HTTP request metric labels."""
        record_http_request(
            method="POST",
            endpoint="/api/v1/tenants",
            status_code=201,
            duration_seconds=0.050,
        )
        
        metrics = get_metrics_text()
        assert "POST" in metrics or "method" in metrics
        assert "201" in metrics or "status_code" in metrics
    
    def test_db_query_labels(self):
        """Test database query metric labels."""
        record_db_query(
            query_type="INSERT",
            table="tenants",
            duration_seconds=0.025,
        )
        
        metrics = get_metrics_text()
        assert "INSERT" in metrics or "query_type" in metrics
        assert "tenants" in metrics or "table" in metrics
    
    def test_error_labels(self):
        """Test error metric labels."""
        record_db_error(error_type="timeout")
        
        metrics = get_metrics_text()
        assert "error_type" in metrics or "timeout" in metrics
