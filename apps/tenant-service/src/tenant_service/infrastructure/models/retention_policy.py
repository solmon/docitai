"""Retention policy models."""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field
from sqlmodel import JSON, Column, Field as SQLField
from sqlmodel import SQLModel, String

from database_core.base import TenantAwareBase
from tenant_service.domain.enums.retention_types import (
    AppliesTo,
    ResourceType,
    RetentionType,
)


class RetentionPolicy(TenantAwareBase, table=True):
    """Retention policy entity for automatic document lifecycle management."""

    __tablename__ = "retention_policies"

    id: Optional[str] = SQLField(default_factory=lambda: str(uuid4()), primary_key=True)
    tenant_id: str = SQLField(..., index=True)
    created_at: datetime = SQLField(default_factory=datetime.utcnow)
    updated_at: datetime = SQLField(default_factory=datetime.utcnow)
    name: str = SQLField(index=True)
    description: Optional[str] = None
    resource_type: ResourceType
    retention_type: RetentionType
    retention_days: int = SQLField(ge=1, le=36500)  # 1 day to 100 years
    applies_to: AppliesTo
    filter_config: dict = SQLField(sa_column=Column(JSON), default={})
    is_active: bool = SQLField(default=True, index=True)
    created_by: UUID
    executed_count: int = SQLField(default=0)


class RetentionPolicyCreate(BaseModel):
    """Request model for creating retention policy."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    resource_type: ResourceType
    retention_type: RetentionType
    retention_days: int = Field(..., ge=1, le=36500)
    applies_to: AppliesTo
    filter_config: Optional[dict] = Field(default_factory=dict)
    is_active: bool = True


class RetentionPolicyUpdate(BaseModel):
    """Request model for updating retention policy."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    retention_days: Optional[int] = Field(None, ge=1, le=36500)
    applies_to: Optional[AppliesTo] = None
    filter_config: Optional[dict] = None
    is_active: Optional[bool] = None


class RetentionPolicyResponse(BaseModel):
    """Response model for retention policy."""

    id: UUID
    tenant_id: UUID
    name: str
    description: Optional[str]
    resource_type: ResourceType
    retention_type: RetentionType
    retention_days: int
    applies_to: AppliesTo
    filter_config: dict
    is_active: bool
    created_by: UUID
    executed_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
