"""JWT token validation and extraction middleware for tenant authentication."""

import logging
from datetime import datetime, timedelta

import jwt
from pydantic import BaseModel


logger = logging.getLogger(__name__)


class TokenPayload(BaseModel):
    """JWT token payload structure."""

    sub: str  # Subject (usually user_id)
    tenant_id: str  # Tenant identifier for multi-tenant isolation
    role: str  # User role (system_admin, tenant_admin, folder_manager)
    email: str | None = None
    permissions: list[str] = []
    exp: int  # Expiration timestamp
    iat: int  # Issued at timestamp

    class Config:
        from_attributes = True


class JWTValidator:
    """
    Validates JWT tokens and extracts token payloads.

    Handles token validation, expiration checking, and payload extraction.
    Enforces tenant context on all authenticated requests.
    """

    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        expiration_hours: int = 24,
    ):
        """
        Initialize JWT validator.

        Args:
            secret_key: Secret key for signing/validating tokens
            algorithm: JWT algorithm (default: HS256)
            expiration_hours: Default token expiration in hours

        """
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.expiration_hours = expiration_hours

    def create_token(
        self,
        user_id: str,
        tenant_id: str,
        role: str,
        email: str | None = None,
        permissions: list[str] | None = None,
    ) -> str:
        """
        Create a new JWT token.

        Args:
            user_id: User identifier
            tenant_id: Tenant identifier
            role: User role
            email: User email (optional)
            permissions: User permissions (optional)

        Returns:
            Encoded JWT token

        """
        now = datetime.utcnow()
        expires = now + timedelta(hours=self.expiration_hours)

        payload = {
            "sub": user_id,
            "tenant_id": tenant_id,
            "role": role,
            "email": email,
            "permissions": permissions or [],
            "iat": int(now.timestamp()),
            "exp": int(expires.timestamp()),
        }

        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

        logger.debug(f"Token created for user {user_id} in tenant {tenant_id}")
        return token

    def validate_token(self, token: str) -> TokenPayload:
        """
        Validate JWT token and extract payload.

        Args:
            token: JWT token string

        Returns:
            TokenPayload with extracted claims

        Raises:
            jwt.InvalidTokenError: If token is invalid or expired

        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            # Verify required fields
            required_fields = ["sub", "tenant_id", "role"]
            for field in required_fields:
                if field not in payload:
                    raise jwt.InvalidTokenError(f"Missing required field: {field}")

            token_data = TokenPayload(**payload)
            logger.debug(f"Token validated for user {token_data.sub}")

            return token_data

        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            raise jwt.InvalidTokenError("Token has expired")
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            raise

    def extract_token_from_header(self, auth_header: str) -> str:
        """
        Extract JWT token from Authorization header.

        Expected format: "Bearer <token>"

        Args:
            auth_header: Authorization header value

        Returns:
            Extracted token string

        Raises:
            ValueError: If header format is invalid

        """
        parts = auth_header.split()

        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise ValueError("Invalid authorization header format. Expected: Bearer <token>")

        return parts[1]
