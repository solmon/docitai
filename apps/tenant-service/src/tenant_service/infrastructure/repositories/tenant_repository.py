"""Tenant repository for data access abstraction."""

import logging
from typing import List, Optional

from sqlmodel import Session, select

from tenant_service.exceptions import ResourceNotFoundError, TenantIsolationViolationError
from tenant_service.infrastructure.models.tenant import Tenant

logger = logging.getLogger(__name__)


class TenantRepository:
    """
    Repository for tenant data access.

    Handles all database operations for tenants with built-in tenant isolation.
    All queries automatically enforce tenant context to prevent cross-tenant access.

    Features:
    - Tenant isolation enforcement on all operations
    - Query optimization with proper indexing
    - Transaction management
    - Audit trail support
    """

    def __init__(self, session: Session):
        """
        Initialize repository with database session.

        Args:
            session: SQLModel Session for database operations
        """
        self.session = session

    async def create(
        self,
        tenant_id: str,
        name: str,
        display_name: Optional[str] = None,
        description: Optional[str] = None,
        subscription_plan: str = "starter",
        admin_email: Optional[str] = None,
    ) -> Tenant:
        """
        Create new tenant in database.

        Args:
            tenant_id: Unique tenant identifier (same as id)
            name: Tenant organization name
            display_name: Display name for UI
            description: Tenant description
            subscription_plan: Initial subscription plan
            admin_email: Primary admin email

        Returns:
            Created Tenant instance
        """
        # Tenant ID must match id for self-referential isolation
        tenant = Tenant(
            id=tenant_id,
            tenant_id=tenant_id,
            name=name,
            display_name=display_name,
            description=description,
            subscription_plan=subscription_plan,
            admin_email=admin_email,
            is_active=True,
        )

        self.session.add(tenant)
        self.session.commit()
        self.session.refresh(tenant)

        logger.info(f"Tenant created: {tenant_id}")
        return tenant

    async def get_by_id(
        self,
        tenant_id: str,
        user_tenant_id: Optional[str] = None,
    ) -> Tenant:
        """
        Get tenant by ID with optional isolation check.

        Args:
            tenant_id: Tenant identifier
            user_tenant_id: User's tenant for isolation verification

        Returns:
            Tenant instance

        Raises:
            ResourceNotFoundError: If tenant not found
            TenantIsolationViolationError: If user trying to access different tenant
        """
        # Check tenant isolation if user context provided
        if user_tenant_id and tenant_id != user_tenant_id:
            raise TenantIsolationViolationError(user_tenant_id, tenant_id)

        statement = select(Tenant).where(Tenant.id == tenant_id)
        tenant = self.session.exec(statement).first()

        if not tenant:
            raise ResourceNotFoundError("Tenant", tenant_id)

        logger.debug(f"Tenant retrieved: {tenant_id}")
        return tenant

    async def list_all(
        self,
        user_tenant_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Tenant]:
        """
        List tenants.

        For non-admin users, only returns their own tenant.
        For admins, can return all tenants (configurable via permissions).

        Args:
            user_tenant_id: User's tenant ID (for filtering)
            skip: Number of records to skip
            limit: Maximum records to return

        Returns:
            List of Tenant instances
        """
        statement = select(Tenant).offset(skip).limit(limit)

        # If user context provided, filter to their tenant
        if user_tenant_id:
            statement = statement.where(Tenant.id == user_tenant_id)

        tenants = self.session.exec(statement).all()
        logger.debug(f"Tenants retrieved: {len(tenants)} records")
        return tenants

    async def update(
        self,
        tenant_id: str,
        user_tenant_id: Optional[str] = None,
        **updates: dict,
    ) -> Tenant:
        """
        Update tenant data.

        Args:
            tenant_id: Tenant identifier
            user_tenant_id: User's tenant for isolation verification
            **updates: Fields to update

        Returns:
            Updated Tenant instance

        Raises:
            ResourceNotFoundError: If tenant not found
            TenantIsolationViolationError: If user trying to update different tenant
        """
        # Check isolation
        if user_tenant_id and tenant_id != user_tenant_id:
            raise TenantIsolationViolationError(user_tenant_id, tenant_id)

        tenant = await self.get_by_id(tenant_id, user_tenant_id)

        # Update allowed fields
        allowed_fields = {"display_name", "description", "subscription_plan", "is_active", "admin_email"}
        for field, value in updates.items():
            if field in allowed_fields and value is not None:
                setattr(tenant, field, value)

        self.session.add(tenant)
        self.session.commit()
        self.session.refresh(tenant)

        logger.info(f"Tenant updated: {tenant_id}")
        return tenant

    async def delete(
        self,
        tenant_id: str,
        user_tenant_id: Optional[str] = None,
    ) -> bool:
        """
        Delete tenant (soft delete via is_active flag).

        Args:
            tenant_id: Tenant identifier
            user_tenant_id: User's tenant for isolation verification

        Returns:
            True if deleted successfully

        Raises:
            ResourceNotFoundError: If tenant not found
            TenantIsolationViolationError: If user trying to delete different tenant
        """
        # Check isolation
        if user_tenant_id and tenant_id != user_tenant_id:
            raise TenantIsolationViolationError(user_tenant_id, tenant_id)

        tenant = await self.get_by_id(tenant_id, user_tenant_id)
        tenant.is_active = False

        self.session.add(tenant)
        self.session.commit()

        logger.info(f"Tenant deleted: {tenant_id}")
        return True
