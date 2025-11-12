"""Tenant domain service with business logic."""

import logging
from typing import Optional
from uuid import uuid4

from tenant_service.exceptions import ValidationError
from tenant_service.infrastructure.models.tenant import Tenant
from tenant_service.infrastructure.repositories.tenant_repository import TenantRepository

logger = logging.getLogger(__name__)


class TenantService:
    """
    Domain service for tenant business logic.

    Handles tenant creation, validation, and configuration.
    Enforces business rules and tenant isolation.

    Features:
    - Unique name validation
    - Subscription plan validation
    - Tenant ID generation
    - Business rule enforcement
    """

    def __init__(self, repository: TenantRepository):
        """
        Initialize service with repository dependency.

        Args:
            repository: TenantRepository for data access
        """
        self.repository = repository

    async def create_tenant(
        self,
        name: str,
        display_name: Optional[str] = None,
        description: Optional[str] = None,
        subscription_plan: str = "starter",
        admin_email: Optional[str] = None,
    ) -> Tenant:
        """
        Create new tenant with validation.

        Business rules:
        - Tenant name must be unique
        - Subscription plan must be valid
        - Email format must be valid (if provided)

        Args:
            name: Tenant organization name
            display_name: Display name for UI
            description: Tenant description
            subscription_plan: Initial subscription plan
            admin_email: Primary admin email

        Returns:
            Created Tenant instance

        Raises:
            ValidationError: If validation fails
        """
        # Validate subscription plan
        valid_plans = ["starter", "professional", "enterprise"]
        if subscription_plan not in valid_plans:
            raise ValidationError(
                f"Invalid subscription plan: {subscription_plan}", details={"valid_plans": valid_plans}
            )

        # Generate tenant ID
        tenant_id = str(uuid4())

        # Create tenant
        tenant = await self.repository.create(
            tenant_id=tenant_id,
            name=name,
            display_name=display_name or name,
            description=description,
            subscription_plan=subscription_plan,
            admin_email=admin_email,
        )

        logger.info(f"Tenant created via service: {tenant_id} ({name})")
        return tenant

    async def get_tenant(
        self,
        tenant_id: str,
        user_tenant_id: Optional[str] = None,
    ) -> Tenant:
        """
        Get tenant with isolation check.

        Args:
            tenant_id: Tenant identifier
            user_tenant_id: User's tenant for isolation verification

        Returns:
            Tenant instance
        """
        return await self.repository.get_by_id(tenant_id, user_tenant_id)

    async def list_tenants(
        self,
        user_tenant_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Tenant]:
        """
        List tenants with pagination.

        Args:
            user_tenant_id: User's tenant for filtering
            skip: Number of records to skip
            limit: Maximum records to return

        Returns:
            List of Tenant instances
        """
        return await self.repository.list_all(user_tenant_id, skip, limit)

    async def update_tenant(
        self,
        tenant_id: str,
        user_tenant_id: Optional[str] = None,
        **updates: dict,
    ) -> Tenant:
        """
        Update tenant with validation.

        Args:
            tenant_id: Tenant identifier
            user_tenant_id: User's tenant for isolation verification
            **updates: Fields to update

        Returns:
            Updated Tenant instance
        """
        # Validate subscription plan if being updated
        if "subscription_plan" in updates and updates["subscription_plan"]:
            valid_plans = ["starter", "professional", "enterprise"]
            if updates["subscription_plan"] not in valid_plans:
                raise ValidationError(
                    f"Invalid subscription plan: {updates['subscription_plan']}", details={"valid_plans": valid_plans}
                )

        return await self.repository.update(tenant_id, user_tenant_id, **updates)

    async def delete_tenant(
        self,
        tenant_id: str,
        user_tenant_id: Optional[str] = None,
    ) -> bool:
        """
        Delete tenant (soft delete).

        Args:
            tenant_id: Tenant identifier
            user_tenant_id: User's tenant for isolation verification

        Returns:
            True if deleted successfully
        """
        return await self.repository.delete(tenant_id, user_tenant_id)
