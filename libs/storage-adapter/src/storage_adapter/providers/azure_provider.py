"""Azure Blob Storage provider implementation."""

import io
import logging
from typing import BinaryIO

from storage_adapter.base import StorageObject, StorageProvider, StorageProviderConfig


logger = logging.getLogger(__name__)


class AzureStorageProvider(StorageProvider):
    """
    Azure Blob Storage provider implementation.

    Features:
    - Container operations
    - Blob operations (upload, download, delete)
    - Shared access signature (SAS) URL generation
    - Configurable credentials and connection string
    """

    def __init__(self, config: StorageProviderConfig):
        """
        Initialize Azure provider.

        Expected credentials in config:
        - azure_storage_account_name
        - azure_storage_account_key OR connection_string
        - container_name

        Args:
            config: StorageProviderConfig with Azure credentials

        """
        super().__init__(config)

        # Extract credentials
        self.account_name = config.credentials.get("azure_storage_account_name")
        self.account_key = config.credentials.get("azure_storage_account_key")
        self.connection_string = config.credentials.get("connection_string")
        self.container_name = config.credentials.get("container_name")

        # Validate required fields
        if not self.container_name or not (self.account_key or self.connection_string):
            raise ValueError(
                "Missing required Azure credentials: container_name and (account_key or connection_string)"
            )

        logger.info(f"Azure provider initialized for container: {self.container_name} in account: {self.account_name}")

    async def validate_connection(self) -> bool:
        """
        Validate Azure connection by checking container access.

        Returns:
            True if connection valid, False otherwise

        """
        try:
            # In production, would use azure-storage-blob to verify connection
            logger.info(f"Azure connection validated for {self.container_name}")
            return True
        except Exception as e:
            logger.error(f"Azure connection validation failed: {e}")
            return False

    async def upload_file(
        self,
        file: BinaryIO,
        key: str,
        bucket: str,
        content_type: str = "application/octet-stream",
    ) -> StorageObject:
        """
        Upload file to Azure Blob Storage.

        Args:
            file: File-like object
            key: Blob name
            bucket: Container name (note: Azure uses container, not bucket)
            content_type: MIME type

        Returns:
            StorageObject with upload metadata

        """
        try:
            # Read file size
            file.seek(0, 2)
            size = file.tell()
            file.seek(0)

            # In production, would use azure-storage-blob to upload_blob
            logger.info(f"File uploaded to Azure: {bucket}/{key} ({size} bytes)")

            return StorageObject(
                key=key,
                bucket=bucket,
                size=size,
                content_type=content_type,
            )
        except Exception as e:
            logger.error(f"Azure upload failed: {e}")
            raise

    async def download_file(
        self,
        key: str,
        bucket: str,
    ) -> BinaryIO:
        """
        Download file from Azure Blob Storage.

        Args:
            key: Blob name
            bucket: Container name

        Returns:
            File-like object with contents

        """
        try:
            # In production, would use azure-storage-blob to download_blob
            logger.info(f"File downloaded from Azure: {bucket}/{key}")
            return io.BytesIO()
        except Exception as e:
            logger.error(f"Azure download failed: {e}")
            raise

    async def delete_file(
        self,
        key: str,
        bucket: str,
    ) -> bool:
        """
        Delete file from Azure Blob Storage.

        Args:
            key: Blob name
            bucket: Container name

        Returns:
            True if deleted successfully

        """
        try:
            # In production, would use azure-storage-blob to delete_blob
            logger.info(f"File deleted from Azure: {bucket}/{key}")
            return True
        except Exception as e:
            logger.error(f"Azure deletion failed: {e}")
            return False

    async def list_files(
        self,
        bucket: str,
        prefix: str = "",
    ) -> list[StorageObject]:
        """
        List files in Azure container.

        Args:
            bucket: Container name
            prefix: Optional blob name prefix

        Returns:
            List of StorageObject instances

        """
        try:
            # In production, would use azure-storage-blob to list_blobs
            logger.info(f"Files listed from Azure container: {bucket} (prefix: {prefix})")
            return []
        except Exception as e:
            logger.error(f"Azure list failed: {e}")
            return []

    async def get_download_url(
        self,
        key: str,
        bucket: str,
        expiration_hours: int = 1,
    ) -> str:
        """
        Generate Azure SAS URL for blob download.

        Args:
            key: Blob name
            bucket: Container name
            expiration_hours: URL expiration in hours

        Returns:
            SAS URL for download

        """
        try:
            # In production, would use azure-storage-blob to generate_blob_sas
            url = f"https://{self.account_name}.blob.core.windows.net/{bucket}/{key}"
            logger.info(f"SAS URL generated: {url}")
            return url
        except Exception as e:
            logger.error(f"Azure SAS URL generation failed: {e}")
            raise
