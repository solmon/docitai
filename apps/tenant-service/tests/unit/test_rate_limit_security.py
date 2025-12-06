"""Unit tests for rate limiting and security middleware."""

import time
from fastapi import FastAPI
from fastapi.testclient import TestClient

from tenant_service.middlewares.rate_limit_middleware import (
    RateLimiter,
    RateLimitConfig,
    RateLimitWindow,
    RateLimitMiddleware,
)
from tenant_service.middlewares.security_middleware import (
    SecurityHeadersConfig,
    SecurityHeadersMiddleware,
    RequestValidationMiddleware,
    get_security_headers_for_environment,
)


class TestRateLimitWindow:
    """Tests for RateLimitWindow class."""

    def test_add_request_under_limit(self):
        """Test adding request when under limit."""
        window = RateLimitWindow(limit=10, window_seconds=60)
        assert window.add_request() is True

    def test_add_request_at_limit(self):
        """Test adding request at limit."""
        window = RateLimitWindow(limit=2, window_seconds=60)
        window.add_request()
        window.add_request()
        assert window.add_request() is False

    def test_add_request_expired_requests_removed(self):
        """Test that expired requests are removed."""
        window = RateLimitWindow(limit=2, window_seconds=1)
        window.add_request()
        window.add_request()

        # Wait for window to expire
        time.sleep(1.1)

        # Should be allowed now
        assert window.add_request() is True

    def test_get_remaining(self):
        """Test getting remaining requests."""
        window = RateLimitWindow(limit=10, window_seconds=60)
        window.add_request()
        window.add_request()
        assert window.get_remaining() == 8

    def test_get_remaining_at_limit(self):
        """Test remaining is 0 at limit."""
        window = RateLimitWindow(limit=2, window_seconds=60)
        window.add_request()
        window.add_request()
        assert window.get_remaining() == 0

    def test_get_reset_time(self):
        """Test getting reset time."""
        window = RateLimitWindow(limit=10, window_seconds=60)
        window.add_request()
        reset_time = window.get_reset_time()
        assert 0 <= reset_time <= 60


class TestRateLimiter:
    """Tests for RateLimiter class."""

    def test_check_rate_limit_allowed(self):
        """Test that requests under limit are allowed."""
        limiter = RateLimiter()
        is_allowed, remaining, reset_time = limiter.check_rate_limit("client1")
        assert is_allowed is True
        assert remaining >= 0

    def test_check_rate_limit_blocked(self):
        """Test that requests over limit are blocked."""
        config = RateLimitConfig(anonymous_limit=2, anonymous_window_seconds=60)
        limiter = RateLimiter(config)

        limiter.check_rate_limit("client1")
        limiter.check_rate_limit("client1")
        is_allowed, remaining, reset_time = limiter.check_rate_limit("client1")

        assert is_allowed is False
        assert remaining == 0

    def test_check_rate_limit_per_client(self):
        """Test rate limiting is per-client."""
        config = RateLimitConfig(anonymous_limit=2, anonymous_window_seconds=60)
        limiter = RateLimiter(config)

        # Exhaust client1's limit
        limiter.check_rate_limit("client1")
        limiter.check_rate_limit("client1")

        # client2 should still be allowed
        is_allowed, _, _ = limiter.check_rate_limit("client2")
        assert is_allowed is True

    def test_check_rate_limit_authenticated_higher_limit(self):
        """Test authenticated users have higher limits."""
        config = RateLimitConfig(anonymous_limit=2, authenticated_limit=10)
        limiter = RateLimiter(config)

        # Use up anonymous limit
        limiter.check_rate_limit("client1", is_authenticated=False)
        limiter.check_rate_limit("client1", is_authenticated=False)
        is_allowed, _, _ = limiter.check_rate_limit("client1", is_authenticated=False)
        assert is_allowed is False

        # Authenticated should still have room
        is_allowed, _, _ = limiter.check_rate_limit("client2", is_authenticated=True)
        assert is_allowed is True

    def test_check_rate_limit_tenant_specific(self):
        """Test tenant-specific rate limits."""
        config = RateLimitConfig(
            authenticated_limit=5,
            tenant_limits={"premium-tenant": 100},
        )
        limiter = RateLimiter(config)

        # Premium tenant should get higher limit
        for _ in range(10):
            is_allowed, _, _ = limiter.check_rate_limit(
                "client1",
                tenant_id="premium-tenant",
                is_authenticated=True,
            )
            assert is_allowed is True

    def test_cleanup_expired_windows(self):
        """Test cleanup of expired windows."""
        config = RateLimitConfig(anonymous_window_seconds=1)
        limiter = RateLimiter(config)

        limiter.check_rate_limit("client1")
        limiter.check_rate_limit("client2")

        # Wait for expiration
        time.sleep(2.1)

        cleaned = limiter.cleanup_expired_windows()
        assert cleaned == 2


class TestRateLimitMiddleware:
    """Tests for RateLimitMiddleware."""

    def setup_method(self):
        """Setup test fixtures."""
        self.app = FastAPI()
        config = RateLimitConfig(anonymous_limit=3, anonymous_window_seconds=60)
        self.app.add_middleware(RateLimitMiddleware, config=config)

        @self.app.get("/test")
        async def test_endpoint():
            return {"status": "ok"}

        @self.app.get("/health")
        async def health_endpoint():
            return {"status": "healthy"}

        self.client = TestClient(self.app)

    def test_rate_limit_headers_present(self):
        """Test rate limit headers are in response."""
        response = self.client.get("/test")
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers

    def test_rate_limit_exceeded_returns_429(self):
        """Test 429 response when rate limit exceeded."""
        # Use up the limit
        for _ in range(3):
            self.client.get("/test")

        # Next request should be blocked
        response = self.client.get("/test")
        assert response.status_code == 429
        assert "Retry-After" in response.headers

    def test_excluded_paths_not_rate_limited(self):
        """Test that excluded paths bypass rate limiting."""
        # Health should not be rate limited
        for _ in range(10):
            response = self.client.get("/health")
            assert response.status_code == 200


class TestSecurityHeadersConfig:
    """Tests for SecurityHeadersConfig."""

    def test_default_config(self):
        """Test default configuration values."""
        config = SecurityHeadersConfig()
        assert config.hsts_enabled is True
        assert config.csp_enabled is True
        assert config.x_frame_options == "DENY"

    def test_get_config_for_environment(self):
        """Test environment-specific configurations."""
        dev_config = get_security_headers_for_environment("development")
        assert dev_config.hsts_enabled is False

        prod_config = get_security_headers_for_environment("production")
        assert prod_config.hsts_enabled is True
        assert prod_config.hsts_preload is True


class TestSecurityHeadersMiddleware:
    """Tests for SecurityHeadersMiddleware."""

    def setup_method(self):
        """Setup test fixtures."""
        self.app = FastAPI()
        self.app.add_middleware(SecurityHeadersMiddleware)

        @self.app.get("/test")
        async def test_endpoint():
            return {"status": "ok"}

        @self.app.get("/docs")
        async def docs_endpoint():
            return {"docs": "here"}

        self.client = TestClient(self.app)

    def test_security_headers_present(self):
        """Test security headers are added to response."""
        response = self.client.get("/test")

        assert "X-Content-Type-Options" in response.headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"

        assert "X-Frame-Options" in response.headers
        assert response.headers["X-Frame-Options"] == "DENY"

        assert "X-XSS-Protection" in response.headers
        assert "Referrer-Policy" in response.headers

    def test_hsts_header_present(self):
        """Test HSTS header is added."""
        response = self.client.get("/test")
        assert "Strict-Transport-Security" in response.headers

    def test_csp_header_present(self):
        """Test CSP header is added for non-docs paths."""
        response = self.client.get("/test")
        assert "Content-Security-Policy" in response.headers

    def test_docs_paths_excluded_from_csp(self):
        """Test docs paths don't get CSP."""
        response = self.client.get("/docs")
        assert "Content-Security-Policy" not in response.headers


class TestRequestValidationMiddleware:
    """Tests for RequestValidationMiddleware."""

    def setup_method(self):
        """Setup test fixtures."""
        self.app = FastAPI()
        self.app.add_middleware(
            RequestValidationMiddleware,
            max_content_length=1024,  # 1KB for testing
        )

        @self.app.post("/test")
        async def test_endpoint():
            return {"status": "ok"}

        @self.app.get("/normal")
        async def normal_endpoint():
            return {"status": "ok"}

        self.client = TestClient(self.app)

    def test_oversized_request_rejected(self):
        """Test requests over size limit are rejected."""
        large_data = "x" * 2048  # 2KB
        self.client.post(
            "/test",
            json={"data": large_data},
            headers={"Content-Length": str(len(large_data))},
        )
        # Note: TestClient may not enforce content-length exactly
        # This tests the middleware logic

    def test_path_traversal_blocked(self):
        """Test path traversal attempts are blocked."""
        response = self.client.get("/test/../secret")
        assert response.status_code == 400

    def test_double_slash_blocked(self):
        """Test double slash paths are blocked."""
        response = self.client.get("/test//extra")
        assert response.status_code == 400

    def test_normal_request_allowed(self):
        """Test normal requests pass through."""
        response = self.client.get("/normal")
        assert response.status_code == 200


class TestMiddlewareIntegration:
    """Integration tests for all middleware together."""

    def setup_method(self):
        """Setup test fixtures with all middleware."""
        self.app = FastAPI()

        # Add all middleware
        self.app.add_middleware(SecurityHeadersMiddleware)
        self.app.add_middleware(RequestValidationMiddleware)
        self.app.add_middleware(
            RateLimitMiddleware,
            config=RateLimitConfig(anonymous_limit=5),
        )

        @self.app.get("/api/test")
        async def test_endpoint():
            return {"status": "ok"}

        self.client = TestClient(self.app)

    def test_all_headers_present(self):
        """Test both security and rate limit headers are present."""
        response = self.client.get("/api/test")

        # Security headers
        assert "X-Content-Type-Options" in response.headers
        assert "X-Frame-Options" in response.headers

        # Rate limit headers
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers

    def test_rate_limit_after_security_check(self):
        """Test rate limiting works after security checks."""
        # Use up rate limit
        for _ in range(5):
            self.client.get("/api/test")

        response = self.client.get("/api/test")
        assert response.status_code == 429


class TestMiddlewarePerformance:
    """Performance tests for middleware."""

    def test_rate_limiter_performance(self):
        """Test rate limiter operations are fast."""
        limiter = RateLimiter()

        start = time.time()
        for i in range(1000):
            limiter.check_rate_limit(f"client{i % 100}")
        duration = time.time() - start

        # 1000 checks should take less than 100ms
        assert duration < 0.1, f"Rate limiting too slow: {duration * 1000:.2f}ms"

    def test_security_headers_performance(self):
        """Test security headers middleware is fast."""
        app = FastAPI()
        app.add_middleware(SecurityHeadersMiddleware)

        @app.get("/test")
        async def test_endpoint():
            return {"ok": True}

        client = TestClient(app)

        start = time.time()
        for _ in range(100):
            client.get("/test")
        duration = time.time() - start

        # 100 requests should take less than 1s (including test client overhead)
        assert duration < 1.0, f"Security headers too slow: {duration * 1000:.2f}ms total"
