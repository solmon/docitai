"""Storage configuration repository."""

import logging
from typing import List, Optional

from sqlmodel import Session, select

from tenant_service.exceptions import ResourceNotFoundError, TenantIsolationViolationError
from tenant_service.infrastructure.models.storage_configuration import StorageConfiguration

logger = logging.getLogger(__name__)


class StorageConfigurationRepository:
    """
    Repository for storage configuration data access.

    Handles all database operations for storage configurations with tenant isolation.
    All queries enforce tenant context to prevent cross-tenant access.
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
        provider_type: str,
        name: str,
        encrypted_credentials: str,
        is_primary: bool = False,
        bucket_name: Optional[str] = None,
        region: Optional[str] = None,
    ) -> StorageConfiguration:
        """
        Create storage configuration.

        Args:
            tenant_id: Tenant identifier
            provider_type: Storage provider type
            name: Configuration name
            encrypted_credentials: Encrypted credentials JSON
            is_primary: Whether this is primary storage
            bucket_name: Provider bucket/container name
            region: Provider region

        Returns:
            Created StorageConfiguration
        """
        config = StorageConfiguration(
            tenant_id=tenant_id,
            provider_type=provider_type,
            name=name,
            encrypted_credentials=encrypted_credentials,
            is_primary=is_primary,
            bucket_name=bucket_name,
            region=region,
            is_active=True,
        )

        self.session.add(config)
        self.session.commit()
        self.session.refresh(config)

        logger.info(f"Storage configuration created: {config.id} for tenant {tenant_id}")
        return config

    async def get_by_id(
        self,
        config_id: str,
        user_tenant_id: Optional[str] = None,
    ) -> StorageConfiguration:
        """
        Get storage configuration by ID.

        Args:
            config_id: Configuration ID
            user_tenant_id: User's tenant for isolation verification

        Returns:
            StorageConfiguration

        Raises:
            ResourceNotFoundError: If not found
        """
        statement = select(StorageConfiguration).where(StorageConfiguration.id == config_id)
        config = self.session.exec(statement).first()

        if not config:
            raise ResourceNotFoundError("StorageConfiguration", config_id)

        # Verify isolation
        if user_tenant_id and config.tenant_id != user_tenant_id:
            raise TenantIsolationViolationError(user_tenant_id, config.tenant_id)

        logger.debug(f"Storage configuration retrieved: {config_id}")
        return config

    async def list_by_tenant(
        self,
        tenant_id: str,
        user_tenant_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[StorageConfiguration]:
        """
        List storage configurations for tenant.

        Args:
            tenant_id: Tenant to list configurations for
            user_tenant_id: User's tenant for isolation verification
            skip: Number of records to skip
            limit: Maximum records to return

        Returns:
            List of StorageConfiguration
        """
        # Verify isolation
        if user_tenant_id and tenant_id != user_tenant_id:
            raise TenantIsolationViolationError(user_tenant_id, tenant_id)

        statement = (
            select(StorageConfiguration).where(StorageConfiguration.tenant_id == tenant_id).offset(skip).limit(limit)
        )

        configs = self.session.exec(statement).all()
        logger.debug(f"Storage configurations listed: {len(configs)} for tenant {tenant_id}")
        return configs

    async def get_primary(
        self,
        tenant_id: str,
        user_tenant_id: Optional[str] = None,
    ) -> Optional[StorageConfiguration]:
        """
        Get primary storage configuration for tenant.

        Args:
            tenant_id: Tenant identifier
            user_tenant_id: User's tenant for isolation verification

        Returns:
            Primary StorageConfiguration or None if not configured
        """
        # Verify isolation
        if user_tenant_id and tenant_id != user_tenant_id:
            raise TenantIsolationViolationError(user_tenant_id, tenant_id)

        statement = select(StorageConfiguration).where(
            StorageConfiguration.tenant_id == tenant_id,
            StorageConfiguration.is_primary == True,
            StorageConfiguration.is_active == True,
        )

        config = self.session.exec(statement).first()
        return config

    async def update(
        self,
        config_id: str,
        user_tenant_id: Optional[str] = None,
        **updates: dict,
    ) -> StorageConfiguration:
        """
        Update storage configuration.

        Args:
            config_id: Configuration ID
            user_tenant_id: User's tenant for isolation verification
            **updates: Fields to update

        Returns:
            Updated StorageConfiguration
        """
        config = await self.get_by_id(config_id, user_tenant_id)

        # Update allowed fields
        allowed_fields = {"name", "is_primary", "is_active", "encrypted_credentials", "region"}

        for field, value in updates.items():
            if field in allowed_fields and value is not None:
                setattr(config, field, value)

        self.session.add(config)
        self.session.commit()
        self.session.refresh(config)

        logger.info(f"Storage configuration updated: {config_id}")
        return config

    async def delete(
        self,
        config_id: str,
        user_tenant_id: Optional[str] = None,
    ) -> bool:
        """
        Delete storage configuration (soft delete).

        Args:
            config_id: Configuration ID
            user_tenant_id: User's tenant for isolation verification

        Returns:
            True if successful
        """
        config = await self.get_by_id(config_id, user_tenant_id)
        config.is_active = False

        self.session.add(config)
        self.session.commit()

        logger.info(f"Storage configuration deleted: {config_id}")
        return True
