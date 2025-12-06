"""Contract tests for Tenant Management Service API.

These tests validate that the API implementation conforms to the OpenAPI
specification defined in specs/001-tenant-management/contracts/openapi.yaml.

Tests cover:
- Response schema validation
- Required fields presence
- Data type validation
- Enum value validation
- Status code validation
"""

import pytest
from typing import Any, Dict
from fastapi.testclient import TestClient
from datetime import datetime


# Schema validators based on OpenAPI specification
class SchemaValidator:
    """Validates response schemas against OpenAPI specification."""

    @staticmethod
    def validate_tenant_response(data: Dict[str, Any]) -> list[str]:
        """
        Validate TenantResponse schema.

        Required fields: tenant_id, name, contact_email, subscription_plan, status, created_at
        """
        errors = []

        # Required fields
        required_fields = ["tenant_id", "name", "contact_email", "subscription_plan", "status", "created_at"]
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")

        # Type validations
        if "tenant_id" in data and not isinstance(data["tenant_id"], str):
            errors.append("tenant_id must be a string")

        if "name" in data and not isinstance(data["name"], str):
            errors.append("name must be a string")

        if "contact_email" in data:
            if not isinstance(data["contact_email"], str):
                errors.append("contact_email must be a string")
            elif "@" not in data["contact_email"]:
                errors.append("contact_email must be a valid email format")

        if "subscription_plan" in data:
            valid_plans = ["basic", "professional", "enterprise"]
            if data["subscription_plan"] not in valid_plans:
                errors.append(f"subscription_plan must be one of: {valid_plans}")

        if "status" in data:
            valid_statuses = ["active", "suspended", "pending_activation", "deactivated"]
            if data["status"] not in valid_statuses:
                errors.append(f"status must be one of: {valid_statuses}")

        if "created_at" in data:
            try:
                # Should be ISO 8601 format
                datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
            except (ValueError, TypeError):
                errors.append("created_at must be a valid ISO 8601 datetime")

        # Settings validation if present
        if "settings" in data and data["settings"]:
            settings_errors = SchemaValidator.validate_tenant_settings(data["settings"])
            errors.extend(settings_errors)

        return errors

    @staticmethod
    def validate_tenant_settings(data: Dict[str, Any]) -> list[str]:
        """Validate TenantSettings schema."""
        errors = []

        if "max_folders" in data:
            if not isinstance(data["max_folders"], int) or data["max_folders"] < 1:
                errors.append("max_folders must be a positive integer")

        if "max_storage_gb" in data:
            if not isinstance(data["max_storage_gb"], int) or data["max_storage_gb"] < 1:
                errors.append("max_storage_gb must be a positive integer")

        if "enable_compliance_audit" in data:
            if not isinstance(data["enable_compliance_audit"], bool):
                errors.append("enable_compliance_audit must be a boolean")

        if "default_retention_days" in data:
            if not isinstance(data["default_retention_days"], int) or data["default_retention_days"] < 30:
                errors.append("default_retention_days must be an integer >= 30")

        return errors

    @staticmethod
    def validate_tenant_list_response(data: Dict[str, Any]) -> list[str]:
        """Validate TenantListResponse schema."""
        errors = []

        if "tenants" not in data:
            errors.append("Missing required field: tenants")
        elif not isinstance(data["tenants"], list):
            errors.append("tenants must be an array")
        else:
            for i, tenant in enumerate(data["tenants"]):
                tenant_errors = SchemaValidator.validate_tenant_response(tenant)
                for err in tenant_errors:
                    errors.append(f"tenants[{i}]: {err}")

        if "pagination" not in data:
            errors.append("Missing required field: pagination")
        elif data["pagination"]:
            pagination_errors = SchemaValidator.validate_pagination_info(data["pagination"])
            errors.extend(pagination_errors)

        return errors

    @staticmethod
    def validate_pagination_info(data: Dict[str, Any]) -> list[str]:
        """Validate PaginationInfo schema."""
        errors = []

        if "page" in data and not isinstance(data["page"], int):
            errors.append("pagination.page must be an integer")

        if "limit" in data and not isinstance(data["limit"], int):
            errors.append("pagination.limit must be an integer")

        if "total" in data and not isinstance(data["total"], int):
            errors.append("pagination.total must be an integer")

        return errors

    @staticmethod
    def validate_folder_response(data: Dict[str, Any]) -> list[str]:
        """Validate FolderResponse schema."""
        errors = []

        required_fields = ["folder_id", "tenant_id", "name", "path", "level", "created_at"]
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")

        if "level" in data and (not isinstance(data["level"], int) or data["level"] < 0):
            errors.append("level must be a non-negative integer")

        if "path" in data and not isinstance(data["path"], str):
            errors.append("path must be a string")

        return errors

    @staticmethod
    def validate_storage_config_response(data: Dict[str, Any]) -> list[str]:
        """Validate StorageConfigResponse schema."""
        errors = []

        required_fields = ["config_id", "tenant_id", "provider_type", "provider_region", "is_active", "created_at"]
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")

        if "provider_type" in data:
            valid_types = ["azure_blob", "aws_s3", "gcs"]
            if data["provider_type"] not in valid_types:
                errors.append(f"provider_type must be one of: {valid_types}")

        if "is_active" in data and not isinstance(data["is_active"], bool):
            errors.append("is_active must be a boolean")

        return errors

    @staticmethod
    def validate_retention_policy_response(data: Dict[str, Any]) -> list[str]:
        """Validate RetentionPolicyResponse schema."""
        errors = []

        required_fields = ["policy_id", "tenant_id", "name", "scope_type", "retention_period_days"]
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")

        if "scope_type" in data:
            valid_scopes = ["tenant", "folder"]
            if data["scope_type"] not in valid_scopes:
                errors.append(f"scope_type must be one of: {valid_scopes}")

        if "retention_period_days" in data:
            if not isinstance(data["retention_period_days"], int) or data["retention_period_days"] < 1:
                errors.append("retention_period_days must be a positive integer")

        if "compliance_framework" in data:
            valid_frameworks = ["gdpr", "hipaa", "sox", "custom"]
            if data["compliance_framework"] not in valid_frameworks:
                errors.append(f"compliance_framework must be one of: {valid_frameworks}")

        return errors

    @staticmethod
    def validate_document_category_response(data: Dict[str, Any]) -> list[str]:
        """Validate DocumentCategoryResponse schema."""
        errors = []

        required_fields = ["category_id", "tenant_id", "name"]
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")

        return errors

    @staticmethod
    def validate_document_type_response(data: Dict[str, Any]) -> list[str]:
        """Validate DocumentTypeResponse schema."""
        errors = []

        required_fields = ["type_id", "tenant_id", "name"]
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")

        if "custom_attributes" in data and not isinstance(data["custom_attributes"], list):
            errors.append("custom_attributes must be an array")

        return errors

    @staticmethod
    def validate_error_response(data: Dict[str, Any]) -> list[str]:
        """Validate ErrorResponse schema."""
        errors = []

        if "error_code" not in data:
            errors.append("Missing required field: error_code")

        if "message" not in data:
            errors.append("Missing required field: message")

        return errors

    @staticmethod
    def validate_health_response(data: Dict[str, Any]) -> list[str]:
        """Validate health check response."""
        errors = []

        if "status" not in data:
            errors.append("Missing required field: status")
        elif data["status"] not in ["healthy", "unhealthy", "degraded"]:
            errors.append("status must be one of: healthy, unhealthy, degraded")

        return errors


class TestTenantEndpointContracts:
    """Contract tests for tenant endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from tenant_service.main import app

        return TestClient(app)

    @pytest.fixture
    def mock_auth_header(self):
        """Mock authorization header."""
        return {"Authorization": "Bearer mock-jwt-token"}

    def test_list_tenants_response_schema(self, client, mock_auth_header):
        """Test GET /tenants response conforms to TenantListResponse schema."""
        response = client.get("/api/v1/tenants", headers=mock_auth_header)

        # Should return 200 or 401/403 for auth issues
        if response.status_code == 200:
            data = response.json()
            errors = SchemaValidator.validate_tenant_list_response(data)
            assert not errors, f"Schema validation errors: {errors}"
        else:
            # Auth failure responses should also be valid
            assert response.status_code in [401, 403, 404]

    def test_create_tenant_response_schema(self, client, mock_auth_header):
        """Test POST /tenants response conforms to TenantResponse schema."""
        create_data = {
            "name": "Test Tenant",
            "contact_email": "test@example.com",
            "subscription_plan": "basic",
        }

        response = client.post("/api/v1/tenants", json=create_data, headers=mock_auth_header)

        if response.status_code == 201:
            data = response.json()
            errors = SchemaValidator.validate_tenant_response(data)
            assert not errors, f"Schema validation errors: {errors}"
        elif response.status_code in [400, 422]:
            # Validation error response
            data = response.json()
            # Should have error structure
            assert "detail" in data or "error_code" in data or "message" in data

    def test_get_tenant_response_schema(self, client, mock_auth_header):
        """Test GET /tenants/{tenantId} response conforms to TenantResponse schema."""
        response = client.get("/api/v1/tenants/test-tenant-id", headers=mock_auth_header)

        if response.status_code == 200:
            data = response.json()
            errors = SchemaValidator.validate_tenant_response(data)
            assert not errors, f"Schema validation errors: {errors}"
        else:
            assert response.status_code in [401, 403, 404]

    def test_create_tenant_validates_required_fields(self, client, mock_auth_header):
        """Test that POST /tenants validates required fields."""
        # Missing required fields
        response = client.post("/api/v1/tenants", json={}, headers=mock_auth_header)

        # Should return 400 or 422 for validation error
        assert response.status_code in [400, 422]

    def test_create_tenant_validates_subscription_plan(self, client, mock_auth_header):
        """Test that POST /tenants validates subscription_plan enum."""
        create_data = {
            "name": "Test Tenant",
            "contact_email": "test@example.com",
            "subscription_plan": "invalid_plan",
        }

        response = client.post("/api/v1/tenants", json=create_data, headers=mock_auth_header)

        # Should return validation error
        assert response.status_code in [400, 422]

    def test_create_tenant_validates_email_format(self, client, mock_auth_header):
        """Test that POST /tenants validates email format."""
        create_data = {
            "name": "Test Tenant",
            "contact_email": "not-an-email",
            "subscription_plan": "basic",
        }

        response = client.post("/api/v1/tenants", json=create_data, headers=mock_auth_header)

        # Should return validation error
        assert response.status_code in [400, 422]


class TestFolderEndpointContracts:
    """Contract tests for folder endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from tenant_service.main import app

        return TestClient(app)

    @pytest.fixture
    def mock_auth_header(self):
        """Mock authorization header."""
        return {"Authorization": "Bearer mock-jwt-token"}

    def test_list_folders_response_schema(self, client, mock_auth_header):
        """Test GET /tenants/{tenantId}/folders response schema."""
        response = client.get("/api/v1/tenants/test-tenant/folders", headers=mock_auth_header)

        if response.status_code == 200:
            data = response.json()
            assert "folders" in data or isinstance(data, list)

    def test_create_folder_validates_required_fields(self, client, mock_auth_header):
        """Test that POST /tenants/{tenantId}/folders validates required fields."""
        response = client.post(
            "/api/v1/tenants/test-tenant/folders",
            json={},
            headers=mock_auth_header,
        )

        assert response.status_code in [400, 422]


class TestStorageEndpointContracts:
    """Contract tests for storage endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from tenant_service.main import app

        return TestClient(app)

    @pytest.fixture
    def mock_auth_header(self):
        """Mock authorization header."""
        return {"Authorization": "Bearer mock-jwt-token"}

    def test_create_storage_config_validates_provider_type(self, client, mock_auth_header):
        """Test that storage config validates provider_type enum."""
        create_data = {
            "provider_type": "invalid_provider",
            "provider_region": "us-east-1",
            "connection_config": {
                "endpoint_url": "https://example.com",
                "access_key": "key",
                "secret_key": "secret",
                "bucket_name": "bucket",
            },
        }

        response = client.post(
            "/api/v1/tenants/test-tenant/storage",
            json=create_data,
            headers=mock_auth_header,
        )

        assert response.status_code in [400, 422]


class TestRetentionPolicyEndpointContracts:
    """Contract tests for retention policy endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from tenant_service.main import app

        return TestClient(app)

    @pytest.fixture
    def mock_auth_header(self):
        """Mock authorization header."""
        return {"Authorization": "Bearer mock-jwt-token"}

    def test_create_retention_policy_validates_scope_type(self, client, mock_auth_header):
        """Test that retention policy validates scope_type enum."""
        create_data = {
            "name": "Test Policy",
            "scope_type": "invalid_scope",
            "retention_period_days": 365,
        }

        response = client.post(
            "/api/v1/tenants/test-tenant/retention-policies",
            json=create_data,
            headers=mock_auth_header,
        )

        assert response.status_code in [400, 422]


class TestHealthEndpointContracts:
    """Contract tests for health endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from tenant_service.main import app

        return TestClient(app)

    def test_health_endpoint_public(self, client):
        """Test that /health is publicly accessible (no auth required)."""
        response = client.get("/health")

        # Should not require auth
        assert response.status_code in [200, 503]

    def test_health_response_schema(self, client):
        """Test /health response schema."""
        response = client.get("/health")

        if response.status_code == 200:
            data = response.json()
            errors = SchemaValidator.validate_health_response(data)
            assert not errors, f"Schema validation errors: {errors}"

    def test_health_ready_endpoint_public(self, client):
        """Test that /health/ready is publicly accessible."""
        response = client.get("/health/ready")

        assert response.status_code in [200, 503]


class TestErrorResponseContracts:
    """Contract tests for error responses."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from tenant_service.main import app

        return TestClient(app)

    def test_404_response_format(self, client):
        """Test that 404 responses follow error schema."""
        response = client.get("/api/v1/tenants/nonexistent-tenant-12345")

        if response.status_code == 404:
            data = response.json()
            # Should have error structure
            assert "detail" in data or "error_code" in data or "message" in data

    def test_422_response_format(self, client):
        """Test that 422 validation error responses follow schema."""
        # Invalid JSON
        response = client.post(
            "/api/v1/tenants",
            json={"invalid_field": True},
        )

        if response.status_code == 422:
            data = response.json()
            # FastAPI validation error format
            assert "detail" in data


class TestSecurityHeaders:
    """Contract tests for security headers."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from tenant_service.main import app

        return TestClient(app)

    def test_security_headers_present(self, client):
        """Test that security headers are present in responses."""
        response = client.get("/health")

        # Should have security headers
        assert "X-Content-Type-Options" in response.headers

    def test_rate_limit_headers_present(self, client):
        """Test that rate limit headers are present."""
        response = client.get("/api/v1/tenants")

        # Rate limit headers should be present for API endpoints
        if response.status_code != 429:
            assert "X-RateLimit-Limit" in response.headers or response.status_code in [401, 403]


class TestContentTypes:
    """Contract tests for content type handling."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from tenant_service.main import app

        return TestClient(app)

    def test_json_content_type_response(self, client):
        """Test that API returns application/json content type."""
        response = client.get("/health")

        content_type = response.headers.get("content-type", "")
        assert "application/json" in content_type

    def test_invalid_content_type_rejected(self, client):
        """Test that invalid content types are rejected."""
        response = client.post(
            "/api/v1/tenants",
            content="not json",
            headers={"Content-Type": "text/plain"},
        )

        # Should reject non-JSON content
        assert response.status_code in [400, 415, 422]
