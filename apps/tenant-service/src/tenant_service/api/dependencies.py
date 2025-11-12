"""FastAPI dependencies for authentication and database access."""

import logging
from typing import Annotated, Optional

from database_core.connection import DatabaseManager
from fastapi import Depends, Header, HTTPException, status
from sqlmodel import Session
from tenant_auth.jwt_validator import JWTValidator
from tenant_auth.rbac import RoleType, UserContext

logger = logging.getLogger(__name__)

# JWT configuration
JWT_SECRET_KEY = "your-super-secret-key-change-in-production"  # Should come from settings
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Initialize JWT validator
jwt_validator = JWTValidator(
    secret_key=JWT_SECRET_KEY,
    algorithm=JWT_ALGORITHM,
    expiration_hours=JWT_EXPIRATION_HOURS,
)


async def get_db_session() -> Session:
    """
    Dependency for database session injection.

    Yields:
        SQLModel Session for database operations
    """
    session = DatabaseManager.get_session()
    try:
        yield session
    finally:
        session.close()


SessionDep = Annotated[Session, Depends(get_db_session)]


async def get_current_user(
    authorization: Optional[str] = Header(None),
) -> UserContext:
    """
    Dependency for extracting and validating user context from JWT token.

    Extracts JWT from Authorization header, validates it, and returns user context.
    Required for all protected endpoints.

    Args:
        authorization: Authorization header value (Bearer <token>)

    Returns:
        UserContext with user identity and permissions

    Raises:
        HTTPException: If token is missing, invalid, or expired
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        token = jwt_validator.extract_token_from_header(authorization)
        token_payload = jwt_validator.validate_token(token)

        # Convert to UserContext with enum conversion
        user_context = UserContext(
            user_id=token_payload.sub,
            tenant_id=token_payload.tenant_id,
            role=RoleType(token_payload.role),
            email=token_payload.email,
            permissions=token_payload.permissions,
        )

        logger.debug(f"User authenticated: {user_context.user_id} in tenant {user_context.tenant_id}")
        return user_context

    except ValueError as e:
        logger.warning(f"Invalid authorization header: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.warning(f"Token validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


UserDep = Annotated[UserContext, Depends(get_current_user)]


async def get_optional_user(
    authorization: Optional[str] = Header(None),
) -> Optional[UserContext]:
    """
    Optional user extraction dependency.

    Similar to get_current_user but doesn't raise exception if token is missing.
    Useful for endpoints that support both authenticated and unauthenticated access.

    Args:
        authorization: Authorization header value (Bearer <token>)

    Returns:
        UserContext if token provided and valid, None otherwise
    """
    if not authorization:
        return None

    try:
        token = jwt_validator.extract_token_from_header(authorization)
        token_payload = jwt_validator.validate_token(token)

        user_context = UserContext(
            user_id=token_payload.sub,
            tenant_id=token_payload.tenant_id,
            role=RoleType(token_payload.role),
            email=token_payload.email,
            permissions=token_payload.permissions,
        )

        return user_context
    except Exception as e:
        logger.debug(f"Optional user extraction failed: {e}")
        return None


OptionalUserDep = Annotated[Optional[UserContext], Depends(get_optional_user)]
