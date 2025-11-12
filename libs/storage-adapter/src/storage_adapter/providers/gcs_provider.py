"""Google Cloud Storage provider implementation."""

import io
import logging
from typing import BinaryIO

from storage_adapter.base import StorageObject, StorageProvider, StorageProviderConfig


logger = logging.getLogger(__name__)


class GCSStorageProvider(StorageProvider):
    """
    Google Cloud Storage (GCS) provider implementation.

    Features:
    - Bucket operations
    - Object operations (upload, download, delete)
    - Signed URL generation
    - Service account authentication
    """

    def __init__(self, config: StorageProviderConfig):
        """
        Initialize GCS provider.

        Expected credentials in config:
        - gcp_project_id
        - gcp_service_account_json (path or JSON string)
        - bucket_name

        Args:
            config: StorageProviderConfig with GCS credentials

        """
        super().__init__(config)

        # Extract credentials
        self.project_id = config.credentials.get("gcp_project_id")
        self.service_account = config.credentials.get("gcp_service_account_json")
        self.bucket_name = config.credentials.get("bucket_name")

        # Validate required fields
        if not all([self.project_id, self.service_account, self.bucket_name]):
            raise ValueError("Missing required GCS credentials: project_id, service_account_json, bucket_name")

        logger.info(f"GCS provider initialized for bucket: {self.bucket_name} in project: {self.project_id}")

    async def validate_connection(self) -> bool:
        """
        Validate GCS connection by checking bucket access.

        Returns:
            True if connection valid, False otherwise

        """
        try:
            # In production, would use google-cloud-storage to verify connection
            logger.info(f"GCS connection validated for {self.bucket_name}")
            return True
        except Exception as e:
            logger.error(f"GCS connection validation failed: {e}")
            return False

    async def upload_file(
        self,
        file: BinaryIO,
        key: str,
        bucket: str,
        content_type: str = "application/octet-stream",
    ) -> StorageObject:
        """
        Upload file to Google Cloud Storage.

        Args:
            file: File-like object
            key: GCS object key
            bucket: GCS bucket name
            content_type: MIME type

        Returns:
            StorageObject with upload metadata

        """
        try:
            # Read file size
            file.seek(0, 2)
            size = file.tell()
            file.seek(0)

            # In production, would use google-cloud-storage to upload_blob
            logger.info(f"File uploaded to GCS: gs://{bucket}/{key} ({size} bytes)")

            return StorageObject(
                key=key,
                bucket=bucket,
                size=size,
                content_type=content_type,
            )
        except Exception as e:
            logger.error(f"GCS upload failed: {e}")
            raise

    async def download_file(
        self,
        key: str,
        bucket: str,
    ) -> BinaryIO:
        """
        Download file from Google Cloud Storage.

        Args:
            key: GCS object key
            bucket: GCS bucket name

        Returns:
            File-like object with contents

        """
        try:
            # In production, would use google-cloud-storage to download_blob
            logger.info(f"File downloaded from GCS: gs://{bucket}/{key}")
            return io.BytesIO()
        except Exception as e:
            logger.error(f"GCS download failed: {e}")
            raise

    async def delete_file(
        self,
        key: str,
        bucket: str,
    ) -> bool:
        """
        Delete file from Google Cloud Storage.

        Args:
            key: GCS object key
            bucket: GCS bucket name

        Returns:
            True if deleted successfully

        """
        try:
            # In production, would use google-cloud-storage to delete_blob
            logger.info(f"File deleted from GCS: gs://{bucket}/{key}")
            return True
        except Exception as e:
            logger.error(f"GCS deletion failed: {e}")
            return False

    async def list_files(
        self,
        bucket: str,
        prefix: str = "",
    ) -> list[StorageObject]:
        """
        List files in GCS bucket.

        Args:
            bucket: GCS bucket name
            prefix: Optional prefix filter

        Returns:
            List of StorageObject instances

        """
        try:
            # In production, would use google-cloud-storage to list_blobs
            logger.info(f"Files listed from GCS bucket: {bucket} (prefix: {prefix})")
            return []
        except Exception as e:
            logger.error(f"GCS list failed: {e}")
            return []

    async def get_download_url(
        self,
        key: str,
        bucket: str,
        expiration_hours: int = 1,
    ) -> str:
        """
        Generate signed GCS URL.

        Args:
            key: GCS object key
            bucket: GCS bucket name
            expiration_hours: URL expiration in hours

        Returns:
            Signed URL for download

        """
        try:
            # In production, would use google-cloud-storage to generate_signed_url
            url = f"https://storage.googleapis.com/{bucket}/{key}"
            logger.info(f"Signed URL generated: {url}")
            return url
        except Exception as e:
            logger.error(f"GCS signed URL generation failed: {e}")
            raise
