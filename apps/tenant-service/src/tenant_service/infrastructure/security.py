"""Security utilities and audit helpers for tenant service.

This module provides security-related utilities including:
- Input sanitization
- Security event logging
- Credential validation
- Security configuration validation
"""

import hashlib
import hmac
import logging
import re
import secrets
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class SecurityEventType(str, Enum):
    """Types of security events for audit logging."""

    AUTH_SUCCESS = "auth_success"
    AUTH_FAILURE = "auth_failure"
    AUTH_TOKEN_EXPIRED = "auth_token_expired"
    AUTH_TOKEN_INVALID = "auth_token_invalid"
    PERMISSION_DENIED = "permission_denied"
    TENANT_ISOLATION_VIOLATION = "tenant_isolation_violation"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    CREDENTIAL_CHANGE = "credential_change"


class SecurityEvent(BaseModel):
    """Security event for audit logging."""

    event_type: SecurityEventType
    timestamp: datetime
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    details: Optional[dict[str, Any]] = None
    severity: str = "info"  # info, warning, error, critical


class SecurityAuditLogger:
    """Logger for security-related events."""

    @staticmethod
    def log_event(event: SecurityEvent) -> None:
        """
        Log a security event.

        Args:
            event: SecurityEvent to log
        """
        log_data = {
            "security_event": True,
            "event_type": event.event_type.value,
            "timestamp": event.timestamp.isoformat(),
            "user_id": event.user_id,
            "tenant_id": event.tenant_id,
            "ip_address": event.ip_address,
            "resource": f"{event.resource_type}:{event.resource_id}" if event.resource_type else None,
            "details": event.details,
        }

        # Log at appropriate level
        if event.severity == "critical":
            logger.critical(f"SECURITY: {event.event_type.value}", extra=log_data)
        elif event.severity == "error":
            logger.error(f"SECURITY: {event.event_type.value}", extra=log_data)
        elif event.severity == "warning":
            logger.warning(f"SECURITY: {event.event_type.value}", extra=log_data)
        else:
            logger.info(f"SECURITY: {event.event_type.value}", extra=log_data)

    @staticmethod
    def log_auth_failure(
        user_id: Optional[str],
        reason: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        """Log authentication failure."""
        SecurityAuditLogger.log_event(
            SecurityEvent(
                event_type=SecurityEventType.AUTH_FAILURE,
                timestamp=datetime.now(timezone.utc),
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                details={"reason": reason},
                severity="warning",
            )
        )

    @staticmethod
    def log_isolation_violation(
        user_id: str,
        user_tenant_id: str,
        target_tenant_id: str,
        resource_type: str,
        resource_id: str,
        ip_address: Optional[str] = None,
    ) -> None:
        """Log tenant isolation violation attempt."""
        SecurityAuditLogger.log_event(
            SecurityEvent(
                event_type=SecurityEventType.TENANT_ISOLATION_VIOLATION,
                timestamp=datetime.now(timezone.utc),
                user_id=user_id,
                tenant_id=user_tenant_id,
                ip_address=ip_address,
                resource_type=resource_type,
                resource_id=resource_id,
                details={
                    "user_tenant_id": user_tenant_id,
                    "target_tenant_id": target_tenant_id,
                    "attempted_action": "access",
                },
                severity="critical",
            )
        )

    @staticmethod
    def log_rate_limit(
        tenant_id: str,
        endpoint: str,
        current_rate: int,
        limit: int,
        ip_address: Optional[str] = None,
    ) -> None:
        """Log rate limit exceeded event."""
        SecurityAuditLogger.log_event(
            SecurityEvent(
                event_type=SecurityEventType.RATE_LIMIT_EXCEEDED,
                timestamp=datetime.now(timezone.utc),
                tenant_id=tenant_id,
                ip_address=ip_address,
                details={
                    "endpoint": endpoint,
                    "current_rate": current_rate,
                    "limit": limit,
                },
                severity="warning",
            )
        )


class InputSanitizer:
    """Utilities for sanitizing user input."""

    # Patterns for dangerous content
    SQL_INJECTION_PATTERNS = [
        r"('|(--)|(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER|EXEC|EXECUTE)\b))",
        r"(\bOR\b.*=.*)",
        r"(\bAND\b.*=.*)",
    ]

    XSS_PATTERNS = [
        r"<script[^>]*>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>",
    ]

    PATH_TRAVERSAL_PATTERNS = [
        r"\.\./",
        r"\.\.\\",
        r"%2e%2e%2f",
        r"%2e%2e/",
    ]

    @classmethod
    def sanitize_string(cls, value: str, max_length: int = 1000) -> str:
        """
        Sanitize a string input.

        Args:
            value: String to sanitize
            max_length: Maximum allowed length

        Returns:
            Sanitized string
        """
        if not value:
            return value

        # Truncate to max length
        sanitized = value[:max_length]

        # Remove null bytes
        sanitized = sanitized.replace("\x00", "")

        # Strip leading/trailing whitespace
        sanitized = sanitized.strip()

        return sanitized

    @classmethod
    def check_sql_injection(cls, value: str) -> bool:
        """
        Check if string contains potential SQL injection.

        Args:
            value: String to check

        Returns:
            True if suspicious content found
        """
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                return True
        return False

    @classmethod
    def check_xss(cls, value: str) -> bool:
        """
        Check if string contains potential XSS content.

        Args:
            value: String to check

        Returns:
            True if suspicious content found
        """
        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                return True
        return False

    @classmethod
    def check_path_traversal(cls, value: str) -> bool:
        """
        Check if string contains path traversal attempt.

        Args:
            value: String to check

        Returns:
            True if suspicious content found
        """
        for pattern in cls.PATH_TRAVERSAL_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                return True
        return False

    @classmethod
    def is_safe_input(cls, value: str) -> tuple[bool, Optional[str]]:
        """
        Comprehensive safety check for input.

        Args:
            value: String to check

        Returns:
            Tuple of (is_safe, reason if not safe)
        """
        if cls.check_sql_injection(value):
            return False, "Potential SQL injection detected"
        if cls.check_xss(value):
            return False, "Potential XSS content detected"
        if cls.check_path_traversal(value):
            return False, "Path traversal attempt detected"
        return True, None


class SecureTokenGenerator:
    """Utilities for generating secure tokens."""

    @staticmethod
    def generate_api_key(prefix: str = "dk") -> str:
        """
        Generate a secure API key.

        Args:
            prefix: Prefix for the key (e.g., 'dk' for docitai key)

        Returns:
            Secure API key string
        """
        random_bytes = secrets.token_bytes(32)
        key_hash = hashlib.sha256(random_bytes).hexdigest()[:32]
        return f"{prefix}_{key_hash}"

    @staticmethod
    def generate_secret(length: int = 32) -> str:
        """
        Generate a secure random secret.

        Args:
            length: Length of the secret

        Returns:
            URL-safe base64 encoded secret
        """
        return secrets.token_urlsafe(length)

    @staticmethod
    def hash_secret(secret: str, salt: Optional[str] = None) -> tuple[str, str]:
        """
        Hash a secret with salt.

        Args:
            secret: Secret to hash
            salt: Optional salt (generated if not provided)

        Returns:
            Tuple of (hash, salt)
        """
        if salt is None:
            salt = secrets.token_hex(16)

        hash_value = hashlib.pbkdf2_hmac(
            "sha256",
            secret.encode(),
            salt.encode(),
            iterations=100000,
        ).hex()

        return hash_value, salt

    @staticmethod
    def verify_secret(secret: str, hash_value: str, salt: str) -> bool:
        """
        Verify a secret against its hash.

        Args:
            secret: Secret to verify
            hash_value: Expected hash
            salt: Salt used for hashing

        Returns:
            True if secret matches
        """
        computed_hash, _ = SecureTokenGenerator.hash_secret(secret, salt)
        return hmac.compare_digest(computed_hash, hash_value)


# Security configuration checklist
SECURITY_CHECKLIST = """
Security Hardening Checklist for Tenant Service
==============================================

Authentication & Authorization:
[x] JWT validation with proper signature verification
[x] Token expiration enforcement
[x] Role-based access control (RBAC) implementation
[x] Tenant isolation on all endpoints
[x] Permission-based authorization

Input Validation:
[x] Request body validation with Pydantic
[x] Path parameter validation
[x] Query parameter validation
[x] SQL injection prevention via parameterized queries
[x] XSS prevention via proper encoding

Network Security:
[x] HTTPS enforcement (via TLS termination)
[x] Security headers (CSP, X-Frame-Options, etc.)
[x] Rate limiting per tenant/IP
[x] CORS configuration

Data Protection:
[x] Sensitive data encryption at rest
[x] Secrets not logged
[x] Connection string encryption
[x] PII handling compliance

Monitoring & Audit:
[x] Security event logging
[x] Authentication attempt logging
[x] Access logging with tenant context
[x] Anomaly detection hooks

Infrastructure:
[x] Non-root container user
[x] Read-only filesystem where possible
[x] Resource limits (CPU, memory)
[x] Health check endpoints
[x] Secrets via environment/K8s secrets
"""
