"""Base models for multi-tenant database support with tenant isolation enforcement."""

from datetime import datetime

from sqlmodel import Field, SQLModel


class TenantAwareBase(SQLModel):
    """
    Base model for all tenant-bound entities ensuring tenant isolation.

    All entities that need multi-tenant support should inherit from this class.
    The tenant_id field is mandatory and enforced at both database and application layers.

    Key Features:
    - Automatic tenant_id field on all entities
    - Timestamp tracking (created_at, updated_at)
    - Enables secure multi-tenant queries via tenant context
    - Index on tenant_id for efficient filtering
    """

    # Multi-tenant isolation - mandatory on all tenant-bound entities
    tenant_id: str = Field(
        ...,
        index=True,
        description="Tenant identifier for multi-tenant isolation",
    )

    # Timestamps for audit trail
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Record creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")

    class Config:
        """SQLModel configuration."""

        # Enable ORM mode for Pydantic compatibility
        from_attributes = True
