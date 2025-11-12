"""Storage configuration command handlers (CQRS application layer)."""

import logging
from dataclasses import dataclass
from typing import Optional

from tenant_service.domain.services.storage_service import StorageConfigurationService
from tenant_service.infrastructure.models.storage_configuration import StorageConfiguration

logger = logging.getLogger(__name__)


@dataclass
class ConfigureStorageCommand:
    """Command to configure storage for tenant."""

    tenant_id: str
    provider_type: str
    name: str
    credentials: dict
    is_primary: bool = False


@dataclass
class UpdateStorageCommand:
    """Command to update storage configuration."""

    config_id: str
    name: Optional[str] = None
    is_primary: Optional[bool] = None
    is_active: Optional[bool] = None
    user_tenant_id: Optional[str] = None


@dataclass
class DeleteStorageCommand:
    """Command to delete storage configuration."""

    config_id: str
    user_tenant_id: Optional[str] = None


class ConfigureStorageHandler:
    """Handler for ConfigureStorageCommand."""

    def __init__(self, service: StorageConfigurationService):
        self.service = service

    async def handle(self, command: ConfigureStorageCommand) -> StorageConfiguration:
        """
        Handle storage configuration command.

        Args:
            command: ConfigureStorageCommand

        Returns:
            Created StorageConfiguration
        """
        config = await self.service.configure_storage(
            tenant_id=command.tenant_id,
            provider_type=command.provider_type,
            name=command.name,
            credentials=command.credentials,
            is_primary=command.is_primary,
        )

        logger.info(f"Storage configuration handled: {config.id}")
        return config


class UpdateStorageHandler:
    """Handler for UpdateStorageCommand."""

    def __init__(self, service: StorageConfigurationService):
        self.service = service

    async def handle(self, command: UpdateStorageCommand) -> StorageConfiguration:
        """
        Handle storage update command.

        Args:
            command: UpdateStorageCommand

        Returns:
            Updated StorageConfiguration
        """
        updates = {
            "name": command.name,
            "is_primary": command.is_primary,
            "is_active": command.is_active,
        }

        config = await self.service.update_configuration(
            config_id=command.config_id,
            user_tenant_id=command.user_tenant_id,
            **{k: v for k, v in updates.items() if v is not None},
        )

        logger.info(f"Storage update handled: {config.id}")
        return config


class DeleteStorageHandler:
    """Handler for DeleteStorageCommand."""

    def __init__(self, service: StorageConfigurationService):
        self.service = service

    async def handle(self, command: DeleteStorageCommand) -> bool:
        """
        Handle storage deletion command.

        Args:
            command: DeleteStorageCommand

        Returns:
            True if successful
        """
        result = await self.service.delete_configuration(
            config_id=command.config_id,
            user_tenant_id=command.user_tenant_id,
        )

        logger.info(f"Storage deletion handled: {command.config_id}")
        return result
