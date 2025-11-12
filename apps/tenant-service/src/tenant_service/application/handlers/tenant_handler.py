"""Tenant command handlers (CQRS application layer)."""

import logging
from dataclasses import dataclass
from typing import Optional

from tenant_service.domain.services.tenant_service import TenantService
from tenant_service.infrastructure.models.tenant import Tenant

logger = logging.getLogger(__name__)


@dataclass
class CreateTenantCommand:
    """Command to create a tenant."""

    name: str
    display_name: Optional[str] = None
    description: Optional[str] = None
    subscription_plan: str = "starter"
    admin_email: Optional[str] = None


@dataclass
class UpdateTenantCommand:
    """Command to update a tenant."""

    tenant_id: str
    display_name: Optional[str] = None
    description: Optional[str] = None
    subscription_plan: Optional[str] = None
    is_active: Optional[bool] = None
    admin_email: Optional[str] = None
    user_tenant_id: Optional[str] = None


@dataclass
class DeleteTenantCommand:
    """Command to delete a tenant."""

    tenant_id: str
    user_tenant_id: Optional[str] = None


class CreateTenantHandler:
    """Handler for CreateTenantCommand."""

    def __init__(self, service: TenantService):
        self.service = service

    async def handle(self, command: CreateTenantCommand) -> Tenant:
        """
        Handle tenant creation command.

        Args:
            command: CreateTenantCommand

        Returns:
            Created Tenant
        """
        tenant = await self.service.create_tenant(
            name=command.name,
            display_name=command.display_name,
            description=command.description,
            subscription_plan=command.subscription_plan,
            admin_email=command.admin_email,
        )

        logger.info(f"Tenant creation handled: {tenant.id}")
        return tenant


class UpdateTenantHandler:
    """Handler for UpdateTenantCommand."""

    def __init__(self, service: TenantService):
        self.service = service

    async def handle(self, command: UpdateTenantCommand) -> Tenant:
        """
        Handle tenant update command.

        Args:
            command: UpdateTenantCommand

        Returns:
            Updated Tenant
        """
        updates = {
            "display_name": command.display_name,
            "description": command.description,
            "subscription_plan": command.subscription_plan,
            "is_active": command.is_active,
            "admin_email": command.admin_email,
        }

        tenant = await self.service.update_tenant(
            tenant_id=command.tenant_id,
            user_tenant_id=command.user_tenant_id,
            **{k: v for k, v in updates.items() if v is not None},
        )

        logger.info(f"Tenant update handled: {tenant.id}")
        return tenant


class DeleteTenantHandler:
    """Handler for DeleteTenantCommand."""

    def __init__(self, service: TenantService):
        self.service = service

    async def handle(self, command: DeleteTenantCommand) -> bool:
        """
        Handle tenant deletion command.

        Args:
            command: DeleteTenantCommand

        Returns:
            True if successful
        """
        result = await self.service.delete_tenant(
            tenant_id=command.tenant_id,
            user_tenant_id=command.user_tenant_id,
        )

        logger.info(f"Tenant deletion handled: {command.tenant_id}")
        return result
