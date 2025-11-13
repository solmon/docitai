"""Compliance audit trail models."""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field
from sqlmodel import JSON, Column, Field as SQLField
from sqlmodel import SQLModel, String

from database_core.base import TenantAwareBase
from tenant_service.domain.enums.retention_types import AuditActionType, ComplianceStatus


class ComplianceAuditTrail(TenantAwareBase, table=True):
    """Immutable audit trail for compliance tracking."""

    __tablename__ = "compliance_audit_trail"

    id: Optional[str] = SQLField(default_factory=lambda: str(uuid4()), primary_key=True)
    tenant_id: str = SQLField(..., index=True)
    created_at: datetime = SQLField(default_factory=datetime.utcnow)
    updated_at: datetime = SQLField(default_factory=datetime.utcnow)
    action_type: AuditActionType = SQLField(index=True)
    resource_type: str = SQLField(index=True)
    resource_id: UUID = SQLField(index=True)
    old_value: Optional[dict] = SQLField(sa_column=Column(JSON), default=None)
    new_value: Optional[dict] = SQLField(sa_column=Column(JSON), default=None)
    changed_by: UUID
    reason: Optional[str] = None
    compliance_status: ComplianceStatus = SQLField(default=ComplianceStatus.SUCCESS)


class ComplianceAuditTrailCreate(BaseModel):
    """Request model for creating audit entry."""

    action_type: AuditActionType
    resource_type: str = Field(..., min_length=1, max_length=50)
    resource_id: UUID
    old_value: Optional[dict] = None
    new_value: Optional[dict] = None
    changed_by: UUID
    reason: Optional[str] = Field(None, max_length=1000)
    compliance_status: Optional[ComplianceStatus] = None


class ComplianceAuditTrailResponse(BaseModel):
    """Response model for audit trail entry."""

    id: UUID
    tenant_id: UUID
    action_type: AuditActionType
    resource_type: str
    resource_id: UUID
    old_value: Optional[dict]
    new_value: Optional[dict]
    changed_by: UUID
    reason: Optional[str]
    compliance_status: ComplianceStatus
    created_at: datetime

    model_config = {"from_attributes": True}
