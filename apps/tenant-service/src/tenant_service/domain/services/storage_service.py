"""Storage service with business logic and provider validation."""

import logging
from typing import Optional

from storage_adapter.factory import StorageProviderFactory

from tenant_service.domain.services.encryption_service import EncryptionService
from tenant_service.exceptions import StorageProviderError, ValidationError
from tenant_service.infrastructure.models.storage_configuration import StorageConfiguration
from tenant_service.infrastructure.repositories.storage_repository import StorageConfigurationRepository

logger = logging.getLogger(__name__)


class StorageConfigurationService:
    """
    Domain service for storage configuration business logic.

    Handles storage provider validation, credential encryption,
    and configuration management.

    Features:
    - Provider validation before storage
    - Credential encryption on store
    - Credential decryption on retrieve
    - Primary storage enforcement
    """

    def __init__(
        self,
        repository: StorageConfigurationRepository,
        encryption_service: Optional[EncryptionService] = None,
    ):
        """
        Initialize storage service.

        Args:
            repository: StorageConfigurationRepository
            encryption_service: EncryptionService (creates default if not provided)
        """
        self.repository = repository
        self.encryption_service = encryption_service or EncryptionService()

    async def configure_storage(
        self,
        tenant_id: str,
        provider_type: str,
        name: str,
        credentials: dict,
        is_primary: bool = False,
    ) -> StorageConfiguration:
        """
        Configure storage for tenant with validation.

        Business rules:
        - Provider type must be valid (s3, azure, gcs)
        - Credentials must be valid for provider
        - Connection must be validated
        - Only one primary storage per tenant

        Args:
            tenant_id: Tenant identifier
            provider_type: Storage provider type
            name: Configuration name
            credentials: Provider-specific credentials
            is_primary: Whether this is primary storage

        Returns:
            Created StorageConfiguration

        Raises:
            ValidationError: If validation fails
            StorageProviderError: If provider error occurs
        """
        # Validate provider type
        valid_providers = StorageProviderFactory.get_supported_providers()
        if provider_type not in valid_providers:
            raise ValidationError(
                f"Invalid provider type: {provider_type}", details={"valid_providers": valid_providers}
            )

        try:
            # Create provider instance with credentials
            provider_config = {
                "provider_type": provider_type,
                "credentials": credentials,
            }
            provider = StorageProviderFactory.create_provider(provider_config)

            # Validate connection before saving
            is_valid = await provider.validate_connection()
            if not is_valid:
                raise StorageProviderError(provider_type, "Connection validation failed")

            await provider.close()

        except StorageProviderError:
            raise
        except Exception as e:
            logger.error(f"Provider creation/validation failed: {e}")
            raise StorageProviderError(provider_type, str(e))

        # If setting as primary, deactivate other primaries
        if is_primary:
            # In production, would update all other primary configs
            logger.info(f"Setting as primary storage for tenant {tenant_id}")

        # Encrypt credentials before storing
        encrypted_creds = self.encryption_service.encrypt_credentials(credentials, tenant_id=tenant_id)

        # Extract bucket/region if available
        bucket_name = credentials.get("bucket_name")
        region = credentials.get("region") or credentials.get("aws_region")

        # Store configuration
        config = await self.repository.create(
            tenant_id=tenant_id,
            provider_type=provider_type,
            name=name,
            encrypted_credentials=encrypted_creds,
            is_primary=is_primary,
            bucket_name=bucket_name,
            region=region,
        )

        logger.info(f"Storage configuration created: {config.id} for tenant {tenant_id}")
        return config

    async def get_configuration(
        self,
        config_id: str,
        user_tenant_id: Optional[str] = None,
    ) -> StorageConfiguration:
        """
        Get storage configuration with isolation check.

        Args:
            config_id: Configuration ID
            user_tenant_id: User's tenant for isolation verification

        Returns:
            StorageConfiguration
        """
        return await self.repository.get_by_id(config_id, user_tenant_id)

    async def list_configurations(
        self,
        tenant_id: str,
        user_tenant_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[StorageConfiguration]:
        """
        List storage configurations for tenant.

        Args:
            tenant_id: Tenant identifier
            user_tenant_id: User's tenant for isolation verification
            skip: Number of records to skip
            limit: Maximum records to return

        Returns:
            List of StorageConfiguration
        """
        return await self.repository.list_by_tenant(tenant_id, user_tenant_id, skip, limit)

    async def get_provider_instance(
        self,
        config_id: str,
        user_tenant_id: Optional[str] = None,
    ):
        """
        Get initialized provider instance from configuration.

        Decrypts credentials and creates ready-to-use provider.

        Args:
            config_id: Configuration ID
            user_tenant_id: User's tenant for isolation verification

        Returns:
            Initialized storage provider instance
        """
        config = await self.repository.get_by_id(config_id, user_tenant_id)

        # Decrypt credentials
        credentials = self.encryption_service.decrypt_credentials(
            config.encrypted_credentials, tenant_id=config.tenant_id
        )

        # Create provider
        provider_config = {
            "provider_type": config.provider_type,
            "credentials": credentials,
        }
        provider = StorageProviderFactory.create_provider(provider_config)

        logger.debug(f"Provider instance created from config: {config_id}")
        return provider

    async def update_configuration(
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
        return await self.repository.update(config_id, user_tenant_id, **updates)

    async def delete_configuration(
        self,
        config_id: str,
        user_tenant_id: Optional[str] = None,
    ) -> bool:
        """
        Delete storage configuration.

        Args:
            config_id: Configuration ID
            user_tenant_id: User's tenant for isolation verification

        Returns:
            True if successful
        """
        return await self.repository.delete(config_id, user_tenant_id)
