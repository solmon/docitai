"""Storage configuration REST API endpoints."""

import logging
from typing import List

from fastapi import APIRouter, status

from tenant_service.api.dependencies import SessionDep, UserDep
from tenant_service.application.handlers.storage_handler import (
    ConfigureStorageCommand,
    ConfigureStorageHandler,
    DeleteStorageCommand,
    DeleteStorageHandler,
    UpdateStorageCommand,
    UpdateStorageHandler,
)
from tenant_service.domain.services.encryption_service import EncryptionService
from tenant_service.domain.services.storage_service import StorageConfigurationService
from tenant_service.infrastructure.models.storage_configuration import (
    StorageConfigurationCreate,
    StorageConfigurationResponse,
    StorageConfigurationUpdate,
)
from tenant_service.infrastructure.repositories.storage_repository import StorageConfigurationRepository
from tenant_service.logging import set_tenant_context, set_user_context

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/storage", tags=["storage"])


@router.post("", response_model=StorageConfigurationResponse, status_code=status.HTTP_201_CREATED)
async def configure_storage(
    config_data: StorageConfigurationCreate,
    user: UserDep,
    session: SessionDep,
):
    """
    Configure storage for tenant.

    Validates provider credentials before saving.
    Encrypts credentials in database.

    **Permission**: STORAGE_UPDATE (Tenant Admin)

    Args:
        config_data: Storage configuration data
        user: Authenticated user context
        session: Database session

    Returns:
        Created storage configuration response
    """
    set_user_context(user.user_id)
    set_tenant_context(user.tenant_id)

    # Create handler
    repository = StorageConfigurationRepository(session)
    encryption_service = EncryptionService()
    service = StorageConfigurationService(repository, encryption_service)
    handler = ConfigureStorageHandler(service)

    # Create command
    command = ConfigureStorageCommand(
        tenant_id=user.tenant_id,
        provider_type=config_data.provider_type.value,
        name=config_data.name,
        credentials=config_data.credentials,
        is_primary=False,
    )

    config = await handler.handle(command)

    logger.info(f"Storage configured: {config.id} for tenant {user.tenant_id}")
    return StorageConfigurationResponse.from_orm(config)


@router.get("/{config_id}", response_model=StorageConfigurationResponse)
async def get_storage_configuration(
    config_id: str,
    user: UserDep,
    session: SessionDep,
):
    """
    Get storage configuration by ID.

    **Permission**: STORAGE_READ

    Args:
        config_id: Storage configuration ID
        user: Authenticated user context
        session: Database session

    Returns:
        Storage configuration response
    """
    set_user_context(user.user_id)
    set_tenant_context(user.tenant_id)

    repository = StorageConfigurationRepository(session)
    encryption_service = EncryptionService()
    service = StorageConfigurationService(repository, encryption_service)

    config = await service.get_configuration(config_id, user_tenant_id=user.tenant_id)

    logger.info(f"Storage configuration retrieved: {config_id}")
    return StorageConfigurationResponse.from_orm(config)


@router.get("", response_model=List[StorageConfigurationResponse])
async def list_storage_configurations(
    user: UserDep,
    session: SessionDep,
    skip: int = 0,
    limit: int = 100,
):
    """
    List storage configurations for tenant.

    **Permission**: STORAGE_READ

    Args:
        user: Authenticated user context
        session: Database session
        skip: Number of records to skip
        limit: Maximum records to return

    Returns:
        List of storage configuration responses
    """
    set_user_context(user.user_id)
    set_tenant_context(user.tenant_id)

    limit = min(limit, 100)

    repository = StorageConfigurationRepository(session)
    encryption_service = EncryptionService()
    service = StorageConfigurationService(repository, encryption_service)

    configs = await service.list_configurations(
        tenant_id=user.tenant_id, user_tenant_id=user.tenant_id, skip=skip, limit=limit
    )

    logger.info(f"Storage configurations listed: {len(configs)} for tenant {user.tenant_id}")
    return [StorageConfigurationResponse.from_orm(c) for c in configs]


@router.put("/{config_id}", response_model=StorageConfigurationResponse)
async def update_storage_configuration(
    config_id: str,
    config_data: StorageConfigurationUpdate,
    user: UserDep,
    session: SessionDep,
):
    """
    Update storage configuration.

    **Permission**: STORAGE_UPDATE (Tenant Admin)

    Args:
        config_id: Storage configuration ID
        config_data: Update data
        user: Authenticated user context
        session: Database session

    Returns:
        Updated storage configuration response
    """
    set_user_context(user.user_id)
    set_tenant_context(user.tenant_id)

    repository = StorageConfigurationRepository(session)
    encryption_service = EncryptionService()
    service = StorageConfigurationService(repository, encryption_service)
    handler = UpdateStorageHandler(service)

    command = UpdateStorageCommand(
        config_id=config_id,
        name=config_data.name,
        is_primary=config_data.is_primary,
        is_active=config_data.is_active,
        user_tenant_id=user.tenant_id,
    )

    config = await handler.handle(command)

    logger.info(f"Storage configuration updated: {config_id}")
    return StorageConfigurationResponse.from_orm(config)


@router.delete("/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_storage_configuration(
    config_id: str,
    user: UserDep,
    session: SessionDep,
):
    """
    Delete storage configuration.

    **Permission**: STORAGE_UPDATE (Tenant Admin)

    Args:
        config_id: Storage configuration ID
        user: Authenticated user context
        session: Database session
    """
    set_user_context(user.user_id)
    set_tenant_context(user.tenant_id)

    repository = StorageConfigurationRepository(session)
    encryption_service = EncryptionService()
    service = StorageConfigurationService(repository, encryption_service)
    handler = DeleteStorageHandler(service)

    command = DeleteStorageCommand(
        config_id=config_id,
        user_tenant_id=user.tenant_id,
    )

    await handler.handle(command)

    logger.info(f"Storage configuration deleted: {config_id}")


@router.post("/{config_id}/validate", response_model=dict)
async def validate_storage_connection(
    config_id: str,
    user: UserDep,
    session: SessionDep,
):
    """
    Validate storage provider connection.

    Tests connectivity to the configured storage provider.

    **Permission**: STORAGE_VALIDATE

    Args:
        config_id: Storage configuration ID
        user: Authenticated user context
        session: Database session

    Returns:
        Validation result with status and message
    """
    set_user_context(user.user_id)
    set_tenant_context(user.tenant_id)

    repository = StorageConfigurationRepository(session)
    encryption_service = EncryptionService()
    service = StorageConfigurationService(repository, encryption_service)

    # Get provider instance
    provider = await service.get_provider_instance(config_id, user_tenant_id=user.tenant_id)

    # Validate connection
    is_valid = await provider.validate_connection()
    await provider.close()

    logger.info(f"Storage connection validated: {config_id} - {is_valid}")

    return {
        "status": "success" if is_valid else "failed",
        "message": "Connection validated" if is_valid else "Connection failed",
        "config_id": config_id,
    }
