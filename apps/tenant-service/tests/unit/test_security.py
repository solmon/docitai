"""Unit tests for security utilities."""

from datetime import datetime, timezone

from tenant_service.infrastructure.security import (
    SecurityEventType,
    SecurityEvent,
    SecurityAuditLogger,
    InputSanitizer,
    SecureTokenGenerator,
)


class TestSecurityEvent:
    """Tests for SecurityEvent model."""

    def test_create_event(self):
        """Create a basic security event."""
        event = SecurityEvent(
            event_type=SecurityEventType.AUTH_SUCCESS,
            timestamp=datetime.now(timezone.utc),
            user_id="user123",
            tenant_id="tenant456",
        )
        assert event.event_type == SecurityEventType.AUTH_SUCCESS
        assert event.user_id == "user123"
        assert event.severity == "info"

    def test_event_with_details(self):
        """Create event with detailed information."""
        event = SecurityEvent(
            event_type=SecurityEventType.PERMISSION_DENIED,
            timestamp=datetime.now(timezone.utc),
            user_id="user123",
            details={"permission": "manage_tenants", "action": "create"},
            severity="warning",
        )
        assert event.details["permission"] == "manage_tenants"
        assert event.severity == "warning"


class TestSecurityAuditLogger:
    """Tests for SecurityAuditLogger."""

    def test_log_auth_failure(self, caplog):
        """Log authentication failure event."""
        with caplog.at_level("WARNING"):
            SecurityAuditLogger.log_auth_failure(
                user_id="user123",
                reason="Invalid credentials",
                ip_address="192.168.1.1",
            )
        # Log should contain security event marker
        assert any("auth_failure" in record.message.lower() for record in caplog.records)

    def test_log_isolation_violation(self, caplog):
        """Log tenant isolation violation."""
        with caplog.at_level("CRITICAL"):
            SecurityAuditLogger.log_isolation_violation(
                user_id="user123",
                user_tenant_id="tenant_a",
                target_tenant_id="tenant_b",
                resource_type="folder",
                resource_id="folder123",
            )
        # Should be logged at critical level
        assert any(record.levelname == "CRITICAL" for record in caplog.records)

    def test_log_rate_limit(self, caplog):
        """Log rate limit exceeded event."""
        with caplog.at_level("WARNING"):
            SecurityAuditLogger.log_rate_limit(
                tenant_id="tenant123",
                endpoint="/api/v1/tenants",
                current_rate=150,
                limit=100,
            )
        assert any("rate_limit" in record.message.lower() for record in caplog.records)


class TestInputSanitizer:
    """Tests for InputSanitizer."""

    def test_sanitize_string_basic(self):
        """Basic string sanitization."""
        result = InputSanitizer.sanitize_string("  Hello World  ")
        assert result == "Hello World"

    def test_sanitize_string_truncate(self):
        """Truncate long strings."""
        long_string = "a" * 2000
        result = InputSanitizer.sanitize_string(long_string, max_length=100)
        assert len(result) == 100

    def test_sanitize_string_null_bytes(self):
        """Remove null bytes."""
        result = InputSanitizer.sanitize_string("Hello\x00World")
        assert "\x00" not in result
        assert result == "HelloWorld"

    def test_check_sql_injection_select(self):
        """Detect SELECT-based SQL injection."""
        assert InputSanitizer.check_sql_injection("' OR 1=1 --")
        assert InputSanitizer.check_sql_injection("'; SELECT * FROM users --")
        assert InputSanitizer.check_sql_injection("UNION SELECT password FROM users")

    def test_check_sql_injection_safe(self):
        """Safe strings should not trigger SQL injection detection."""
        assert not InputSanitizer.check_sql_injection("John Doe")
        assert not InputSanitizer.check_sql_injection("user@example.com")
        assert not InputSanitizer.check_sql_injection("My Company Inc.")

    def test_check_xss_script(self):
        """Detect script-based XSS."""
        assert InputSanitizer.check_xss("<script>alert('xss')</script>")
        assert InputSanitizer.check_xss('javascript:alert("xss")')
        assert InputSanitizer.check_xss('<img onerror="alert(1)">')

    def test_check_xss_safe(self):
        """Safe strings should not trigger XSS detection."""
        assert not InputSanitizer.check_xss("Normal text content")
        assert not InputSanitizer.check_xss("Hello <b>World</b>")  # Not script

    def test_check_path_traversal(self):
        """Detect path traversal attempts."""
        assert InputSanitizer.check_path_traversal("../../../etc/passwd")
        assert InputSanitizer.check_path_traversal("..\\..\\windows\\system32")
        assert InputSanitizer.check_path_traversal("%2e%2e%2f")

    def test_check_path_traversal_safe(self):
        """Safe paths should not trigger detection."""
        assert not InputSanitizer.check_path_traversal("/documents/invoices")
        assert not InputSanitizer.check_path_traversal("folder/subfolder")

    def test_is_safe_input_comprehensive(self):
        """Comprehensive safety check."""
        # Safe input
        is_safe, reason = InputSanitizer.is_safe_input("Normal user input")
        assert is_safe
        assert reason is None

        # SQL injection
        is_safe, reason = InputSanitizer.is_safe_input("'; DROP TABLE users; --")
        assert not is_safe
        assert "SQL injection" in reason

        # XSS
        is_safe, reason = InputSanitizer.is_safe_input("<script>evil()</script>")
        assert not is_safe
        assert "XSS" in reason

        # Path traversal
        is_safe, reason = InputSanitizer.is_safe_input("../../etc/passwd")
        assert not is_safe
        assert "traversal" in reason


class TestSecureTokenGenerator:
    """Tests for SecureTokenGenerator."""

    def test_generate_api_key_format(self):
        """Generated API key has correct format."""
        key = SecureTokenGenerator.generate_api_key()
        assert key.startswith("dk_")
        assert len(key) == 35  # dk_ + 32 hex chars

    def test_generate_api_key_custom_prefix(self):
        """API key with custom prefix."""
        key = SecureTokenGenerator.generate_api_key(prefix="test")
        assert key.startswith("test_")

    def test_generate_api_key_uniqueness(self):
        """Each generated key should be unique."""
        keys = [SecureTokenGenerator.generate_api_key() for _ in range(100)]
        assert len(set(keys)) == 100

    def test_generate_secret_length(self):
        """Generated secret has correct length."""
        secret = SecureTokenGenerator.generate_secret(32)
        # URL-safe base64 encoding expands the length
        assert len(secret) >= 32

    def test_hash_secret_reproducible(self):
        """Hashing with same salt produces same hash."""
        secret = "my_secret_password"
        hash1, salt = SecureTokenGenerator.hash_secret(secret)
        hash2, _ = SecureTokenGenerator.hash_secret(secret, salt)
        assert hash1 == hash2

    def test_hash_secret_different_salts(self):
        """Different salts produce different hashes."""
        secret = "my_secret_password"
        hash1, salt1 = SecureTokenGenerator.hash_secret(secret)
        hash2, salt2 = SecureTokenGenerator.hash_secret(secret)
        assert salt1 != salt2
        assert hash1 != hash2

    def test_verify_secret_correct(self):
        """Verify correct secret."""
        secret = "my_secret_password"
        hash_value, salt = SecureTokenGenerator.hash_secret(secret)
        assert SecureTokenGenerator.verify_secret(secret, hash_value, salt)

    def test_verify_secret_incorrect(self):
        """Reject incorrect secret."""
        secret = "my_secret_password"
        hash_value, salt = SecureTokenGenerator.hash_secret(secret)
        assert not SecureTokenGenerator.verify_secret("wrong_password", hash_value, salt)
