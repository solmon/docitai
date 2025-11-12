"""Storage configuration entity model."""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4

from database_core.base import TenantAwareBase
from sqlmodel import Column, Field, SQLModel, String


class StorageProviderType(str, Enum):
    """Supported storage provider types."""

    S3 = "s3"
    AZURE = "azure"
    GCS = "gcs"


class StorageConfiguration(TenantAwareBase, table=True):
    """
    Storage configuration entity for tenant-specific storage setup.

    Each tenant can configure one or more storage providers.
    Credentials are encrypted before storage.

    Attributes:
        id: Primary key
        tenant_id: Tenant identifier (multi-tenant isolation)
        provider_type: Storage provider type (s3, azure, gcs)
        name: Configuration name for display
        is_primary: Whether this is the primary storage
        is_active: Whether configuration is active
        encrypted_credentials: Encrypted provider credentials
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    id: Optional[str] = Field(
        default_factory=lambda: str(uuid4()), primary_key=True, description="Storage configuration ID"
    )

    # Provider info
    provider_type: StorageProviderType = Field(
        ..., sa_column=Column(String, nullable=False), description="Storage provider type"
    )
    name: str = Field(..., sa_column=Column(String, nullable=False), description="Configuration name")

    # Status
    is_primary: bool = Field(
        default=False, sa_column=Column(String, nullable=False), description="Whether this is primary storage"
    )
    is_active: bool = Field(
        default=True,
        sa_column=Column(String, nullable=False, index=True),
        description="Whether configuration is active",
    )

    # Credentials (encrypted)
    encrypted_credentials: str = Field(
        ..., sa_column=Column(String, nullable=False), description="Encrypted credentials JSON"
    )

    # Metadata
    bucket_name: Optional[str] = Field(None, sa_column=Column(String), description="Provider bucket/container name")
    region: Optional[str] = Field(None, sa_column=Column(String), description="Provider region (if applicable)")

    class Config:
        from_attributes = True


class StorageConfigurationCreate(SQLModel):
    """Request model for creating storage configuration."""

    provider_type: StorageProviderType
    name: str = Field(..., min_length=1, max_length=255)
    is_primary: bool = Field(default=False)
    # Credentials provided as plain JSON in request - encrypted before storage
    credentials: dict = Field(..., description="Provider-specific credentials")


class StorageConfigurationUpdate(SQLModel):
    """Request model for updating storage configuration."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    is_primary: Optional[bool] = None
    is_active: Optional[bool] = None
    credentials: Optional[dict] = None


class StorageConfigurationResponse(SQLModel):
    """Response model for storage configuration."""

    id: str
    tenant_id: str
    provider_type: StorageProviderType
    name: str
    is_primary: bool
    is_active: bool
    bucket_name: Optional[str]
    region: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
