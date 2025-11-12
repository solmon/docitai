"""Factory for creating storage provider instances."""

import logging
from enum import Enum


logger = logging.getLogger(__name__)


class ProviderType(str, Enum):
    """Supported storage provider types."""

    S3 = "s3"
    AZURE = "azure"
    GCS = "gcs"


class StorageProviderFactory:
    """
    Factory for creating storage provider instances.

    Provides centralized provider creation and validation.
    Enables provider-agnostic instantiation based on configuration.
    """

    # Provider registry mapping provider types to implementation classes
    _providers: dict[ProviderType, type] = {}

    @classmethod
    def register_provider(
        cls,
        provider_type: ProviderType,
        provider_class: type,
    ) -> None:
        """
        Register a storage provider implementation.

        Args:
            provider_type: Provider type identifier
            provider_class: Provider implementation class

        """
        cls._providers[provider_type] = provider_class
        logger.info(f"Storage provider registered: {provider_type} -> {provider_class.__name__}")

    @classmethod
    def create_provider(cls, config: dict):
        """
        Create storage provider instance from configuration.

        Args:
            config: Configuration dict with 'provider_type' and provider-specific settings

        Returns:
            Instantiated storage provider

        Raises:
            ValueError: If provider type not supported or configuration invalid

        """
        provider_type_str = config.get("provider_type")

        if not provider_type_str:
            raise ValueError("provider_type is required in config")

        try:
            provider_type = ProviderType(provider_type_str)
        except ValueError:
            raise ValueError(f"Unknown provider type: {provider_type_str}")

        provider_class = cls._providers.get(provider_type)
        if not provider_class:
            raise ValueError(f"Provider {provider_type} is registered but not yet implemented")

        logger.info(f"Creating storage provider: {provider_type}")
        return provider_class(config)

    @classmethod
    def get_supported_providers(cls) -> list[str]:
        """
        Get list of supported provider types.

        Returns:
            List of supported provider type strings

        """
        return [p.value for p in ProviderType]


# Placeholder provider classes (to be implemented in Phase 4)
class S3StorageProvider:
    """AWS S3 storage provider implementation."""

    def __init__(self, config: dict):
        self.config = config
        self.provider_type = "s3"


class AzureStorageProvider:
    """Azure Blob Storage provider implementation."""

    def __init__(self, config: dict):
        self.config = config
        self.provider_type = "azure"


class GCSStorageProvider:
    """Google Cloud Storage provider implementation."""

    def __init__(self, config: dict):
        self.config = config
        self.provider_type = "gcs"


# Register default providers
StorageProviderFactory.register_provider(ProviderType.S3, S3StorageProvider)
StorageProviderFactory.register_provider(ProviderType.AZURE, AzureStorageProvider)
StorageProviderFactory.register_provider(ProviderType.GCS, GCSStorageProvider)
