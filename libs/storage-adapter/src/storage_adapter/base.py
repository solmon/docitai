"""Abstract base interface for storage providers."""

import logging
from abc import ABC, abstractmethod
from typing import Any, BinaryIO

from pydantic import BaseModel


logger = logging.getLogger(__name__)


class StorageProviderConfig(BaseModel):
    """Base configuration for storage providers."""

    provider_type: str
    credentials: dict[str, str]

    class Config:
        from_attributes = True


class StorageObject(BaseModel):
    """Represents a stored object."""

    key: str
    bucket: str
    size: int
    content_type: str
    created_at: str | None = None
    last_modified: str | None = None

    class Config:
        from_attributes = True


class StorageProvider(ABC):
    """
    Abstract base class for cloud storage providers.

    Defines the interface that all storage implementations must follow.
    Enables provider-agnostic storage operations across S3, Azure, GCS, etc.

    Features:
    - Multi-cloud abstraction with consistent interface
    - Credential encryption support
    - Connection validation before operations
    - Unified error handling
    """

    def __init__(self, config: StorageProviderConfig):
        """
        Initialize storage provider with configuration.

        Args:
            config: Provider-specific configuration including encrypted credentials

        """
        self.config = config
        self.provider_type = config.provider_type
        self._client: Any | None = None

    @abstractmethod
    async def validate_connection(self) -> bool:
        """
        Validate connection to storage service.

        Returns:
            True if connection is valid, False otherwise

        """
        pass

    @abstractmethod
    async def upload_file(
        self,
        file: BinaryIO,
        key: str,
        bucket: str,
        content_type: str = "application/octet-stream",
    ) -> StorageObject:
        """
        Upload file to storage.

        Args:
            file: File-like object to upload
            key: Storage key/path for the file
            bucket: Bucket/container name
            content_type: MIME type of the file

        Returns:
            StorageObject with upload metadata

        """
        pass

    @abstractmethod
    async def download_file(
        self,
        key: str,
        bucket: str,
    ) -> BinaryIO:
        """
        Download file from storage.

        Args:
            key: Storage key/path for the file
            bucket: Bucket/container name

        Returns:
            File-like object with file contents

        """
        pass

    @abstractmethod
    async def delete_file(
        self,
        key: str,
        bucket: str,
    ) -> bool:
        """
        Delete file from storage.

        Args:
            key: Storage key/path for the file
            bucket: Bucket/container name

        Returns:
            True if deletion successful, False otherwise

        """
        pass

    @abstractmethod
    async def list_files(
        self,
        bucket: str,
        prefix: str = "",
    ) -> list[StorageObject]:
        """
        List files in bucket with optional prefix filtering.

        Args:
            bucket: Bucket/container name
            prefix: Optional prefix to filter results

        Returns:
            List of StorageObject representing files

        """
        pass

    @abstractmethod
    async def get_download_url(
        self,
        key: str,
        bucket: str,
        expiration_hours: int = 1,
    ) -> str:
        """
        Generate signed download URL for file.

        Args:
            key: Storage key/path for the file
            bucket: Bucket/container name
            expiration_hours: URL expiration time in hours

        Returns:
            Signed URL for file download

        """
        pass

    async def close(self) -> None:
        """Close connection to storage service."""
        if self._client:
            self._client = None
            logger.info(f"Storage connection closed: {self.provider_type}")
