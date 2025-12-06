"""Master Data Version Entity - Audit Trail and Versioning

Immutable append-only record of all master data changes for compliance and rollback.
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID, uuid4

from sqlmodel import Column, JSON, Field, SQLModel

from database_core import TenantAwareBase


class MasterDataVersion(TenantAwareBase, table=True):
    """Master Data Version - Immutable Audit Trail

    Records all changes to master data (categories, types) for:
    - Complete audit trail
    - Version history tracking
    - Rollback capability
    - Compliance requirements
    """

    __tablename__ = "master_data_versions"

    id: Optional[str] = Field(
        default_factory=lambda: str(uuid4()),
        primary_key=True,
        description="Version record ID",
    )
    tenant_id: str = Field(
        ...,
        index=True,
        description="Tenant identifier for multi-tenant isolation",
    )
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Record creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    entity_type: str = Field(
        ...,
        description="Entity type: 'category' or 'type'",
        index=True,
    )
    entity_id: UUID = Field(
        ...,
        description="ID of the entity being versioned",
        index=True,
    )
    version_number: int = Field(
        default=1,
        description="Version number (incremental)",
        ge=1,
    )
    entity_name: str = Field(
        ...,
        description="Entity name at time of version",
        max_length=255,
    )
    action: str = Field(
        ...,
        description="Action that created this version: create, update, delete, restore",
    )
    previous_values: Optional[dict[str, Any]] = Field(
        None,
        description="Previous field values for updates",
        sa_column=Column(JSON),
    )
    new_values: dict[str, Any] = Field(
        ...,
        description="New field values",
        sa_column=Column(JSON),
    )
    changed_fields: list[str] = Field(
        default_factory=list,
        description="List of field names that changed",
        sa_column=Column(JSON),
    )
    changed_by: Optional[str] = Field(
        None,
        description="User ID or system user who made the change",
        max_length=255,
    )
    change_reason: Optional[str] = Field(
        None,
        description="Reason for the change",
        max_length=500,
    )

    # Indexes handled via field index=True


class MasterDataVersionCreate(SQLModel):
    """Create Master Data Version Request"""

    entity_type: str = Field(
        ...,
        description="Entity type: 'category' or 'type'",
    )
    entity_id: UUID = Field(..., description="Entity ID")
    entity_name: str = Field(..., description="Entity name")
    action: str = Field(
        ...,
        description="Action: create, update, delete, restore",
    )
    previous_values: Optional[dict[str, Any]] = None
    new_values: dict[str, Any] = Field(..., description="New values")
    changed_fields: list[str] = Field(default_factory=list)
    changed_by: Optional[str] = None
    change_reason: Optional[str] = None


class MasterDataVersionResponse(SQLModel):
    """Master Data Version Response"""

    id: UUID = Field(..., description="Version ID")
    tenant_id: UUID = Field(..., description="Tenant ID")
    entity_type: str = Field(..., description="Entity type")
    entity_id: UUID = Field(..., description="Entity ID")
    version_number: int = Field(..., description="Version number")
    entity_name: str = Field(..., description="Entity name")
    action: str = Field(..., description="Action")
    previous_values: Optional[dict[str, Any]] = None
    new_values: dict[str, Any] = Field(..., description="New values")
    changed_fields: list[str] = Field(default_factory=list)
    changed_by: Optional[str] = None
    change_reason: Optional[str] = None
    created_at: str = Field(..., description="Creation timestamp")


class MasterDataVersionHistory(SQLModel):
    """Complete version history for an entity"""

    entity_id: UUID = Field(..., description="Entity ID")
    entity_type: str = Field(..., description="Entity type")
    entity_name: str = Field(..., description="Entity name")
    total_versions: int = Field(..., description="Total number of versions")
    versions: list[MasterDataVersionResponse] = Field(
        default_factory=list,
        description="All versions in order",
    )
