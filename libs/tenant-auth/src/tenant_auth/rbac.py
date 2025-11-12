"""Role-Based Access Control (RBAC) models and validation."""

import logging
from collections.abc import Callable
from enum import Enum
from typing import Any

from pydantic import BaseModel


logger = logging.getLogger(__name__)


class RoleType(str, Enum):
    """Supported user roles in the system."""

    SYSTEM_ADMIN = "system_admin"  # Full system access
    TENANT_ADMIN = "tenant_admin"  # Tenant-level administration
    FOLDER_MANAGER = "folder_manager"  # Folder and document management


class PermissionType(str, Enum):
    """Permission types for fine-grained access control."""

    # Tenant permissions
    TENANT_CREATE = "tenant:create"
    TENANT_READ = "tenant:read"
    TENANT_UPDATE = "tenant:update"
    TENANT_DELETE = "tenant:delete"

    # Storage permissions
    STORAGE_READ = "storage:read"
    STORAGE_UPDATE = "storage:update"
    STORAGE_VALIDATE = "storage:validate"

    # Folder permissions
    FOLDER_CREATE = "folder:create"
    FOLDER_READ = "folder:read"
    FOLDER_UPDATE = "folder:update"
    FOLDER_DELETE = "folder:delete"

    # Compliance permissions
    COMPLIANCE_READ = "compliance:read"
    COMPLIANCE_UPDATE = "compliance:update"
    COMPLIANCE_DELETE = "compliance:delete"

    # Master data permissions
    MASTER_DATA_MANAGE = "master_data:manage"


# Role to permissions mapping
ROLE_PERMISSIONS = {
    RoleType.SYSTEM_ADMIN: [
        # System admins have all permissions
        PermissionType.TENANT_CREATE,
        PermissionType.TENANT_READ,
        PermissionType.TENANT_UPDATE,
        PermissionType.TENANT_DELETE,
        PermissionType.STORAGE_READ,
        PermissionType.STORAGE_UPDATE,
        PermissionType.STORAGE_VALIDATE,
        PermissionType.FOLDER_CREATE,
        PermissionType.FOLDER_READ,
        PermissionType.FOLDER_UPDATE,
        PermissionType.FOLDER_DELETE,
        PermissionType.COMPLIANCE_READ,
        PermissionType.COMPLIANCE_UPDATE,
        PermissionType.COMPLIANCE_DELETE,
        PermissionType.MASTER_DATA_MANAGE,
    ],
    RoleType.TENANT_ADMIN: [
        # Tenant admins manage within their tenant
        PermissionType.TENANT_READ,
        PermissionType.TENANT_UPDATE,
        PermissionType.STORAGE_READ,
        PermissionType.STORAGE_UPDATE,
        PermissionType.STORAGE_VALIDATE,
        PermissionType.FOLDER_CREATE,
        PermissionType.FOLDER_READ,
        PermissionType.FOLDER_UPDATE,
        PermissionType.FOLDER_DELETE,
        PermissionType.COMPLIANCE_READ,
        PermissionType.COMPLIANCE_UPDATE,
        PermissionType.MASTER_DATA_MANAGE,
    ],
    RoleType.FOLDER_MANAGER: [
        # Folder managers handle document operations
        PermissionType.FOLDER_READ,
        PermissionType.FOLDER_UPDATE,
        PermissionType.MASTER_DATA_MANAGE,
    ],
}


class UserContext(BaseModel):
    """User context extracted from JWT token."""

    user_id: str
    tenant_id: str
    role: RoleType
    email: str | None = None
    permissions: list[PermissionType] = []

    class Config:
        from_attributes = True


class RBACValidator:
    """
    Validates user permissions against required actions.

    Ensures users can only access resources within their tenant
    and have appropriate permissions for operations.
    """

    @staticmethod
    def get_role_permissions(role: RoleType) -> list[PermissionType]:
        """
        Get all permissions for a given role.

        Args:
            role: User role

        Returns:
            List of permissions for the role

        """
        return ROLE_PERMISSIONS.get(role, [])

    @staticmethod
    def has_permission(user_context: UserContext, required_permission: PermissionType) -> bool:
        """
        Check if user has a specific permission.

        Args:
            user_context: User context from JWT
            required_permission: Required permission

        Returns:
            True if user has permission, False otherwise

        """
        role_permissions = RBACValidator.get_role_permissions(user_context.role)
        has_perm = required_permission in role_permissions

        if not has_perm:
            logger.warning(
                f"Permission denied for user {user_context.user_id}: "
                f"required {required_permission}, role {user_context.role}"
            )

        return has_perm

    @staticmethod
    def verify_tenant_isolation(user_tenant_id: str, resource_tenant_id: str) -> bool:
        """
        Verify user can access resource in their tenant.

        Args:
            user_tenant_id: User's tenant identifier
            resource_tenant_id: Resource's tenant identifier

        Returns:
            True if user can access resource, False otherwise

        """
        has_access = user_tenant_id == resource_tenant_id

        if not has_access:
            logger.warning(
                f"Tenant isolation violation: user tenant {user_tenant_id} "
                f"accessing resource in tenant {resource_tenant_id}"
            )

        return has_access

    @staticmethod
    def require_permission(permission: PermissionType):
        """
        Decorator for endpoint authorization.

        Usage:
            @app.get("/tenants")
            @require_permission(PermissionType.TENANT_READ)
            async def list_tenants(user: UserContext = Depends(get_current_user)):
                ...

        Args:
            permission: Required permission

        Returns:
            Decorator function

        """

        def decorator(func: Callable) -> Callable:
            async def wrapper(*args: Any, **kwargs: Any) -> Any:
                # This is a marker decorator - actual permission check
                # happens in middleware
                return await func(*args, **kwargs)

            wrapper.__permission_required__ = permission  # type: ignore
            return wrapper

        return decorator
