"""Compliance audit trail repository - immutable append-only audit log."""

from typing import Optional
from uuid import UUID

from sqlmodel import Session, select

from tenant_service.domain.enums.retention_types import AuditActionType, ComplianceStatus
from tenant_service.infrastructure.models.compliance_audit_trail import ComplianceAuditTrail


class ComplianceAuditRepository:
    """Repository for compliance audit trail - immutable append-only."""

    def log_action(
        self,
        db: Session,
        user_tenant_id: UUID,
        action_type: AuditActionType,
        resource_type: str,
        resource_id: UUID,
        changed_by: UUID,
        old_value: Optional[dict] = None,
        new_value: Optional[dict] = None,
        reason: Optional[str] = None,
        compliance_status: ComplianceStatus = ComplianceStatus.SUCCESS,
    ) -> ComplianceAuditTrail:
        """Log action to immutable audit trail."""
        audit_entry = ComplianceAuditTrail(
            tenant_id=user_tenant_id,
            action_type=action_type,
            resource_type=resource_type,
            resource_id=resource_id,
            changed_by=changed_by,
            old_value=old_value,
            new_value=new_value,
            reason=reason,
            compliance_status=compliance_status,
        )
        db.add(audit_entry)
        db.commit()
        db.refresh(audit_entry)
        return audit_entry

    def list_by_resource(
        self,
        db: Session,
        user_tenant_id: UUID,
        resource_type: str,
        resource_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ComplianceAuditTrail]:
        """Get audit trail for specific resource."""
        statement = (
            select(ComplianceAuditTrail)
            .where(
                (ComplianceAuditTrail.tenant_id == user_tenant_id)
                & (ComplianceAuditTrail.resource_type == resource_type)
                & (ComplianceAuditTrail.resource_id == resource_id)
            )
            .order_by(ComplianceAuditTrail.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return db.exec(statement).all()

    def list_by_tenant(
        self,
        db: Session,
        user_tenant_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ComplianceAuditTrail]:
        """Get all audit entries for tenant."""
        statement = (
            select(ComplianceAuditTrail)
            .where(ComplianceAuditTrail.tenant_id == user_tenant_id)
            .order_by(ComplianceAuditTrail.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return db.exec(statement).all()

    def list_by_action_type(
        self,
        db: Session,
        user_tenant_id: UUID,
        action_type: AuditActionType,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ComplianceAuditTrail]:
        """Filter audit entries by action type."""
        statement = (
            select(ComplianceAuditTrail)
            .where(
                (ComplianceAuditTrail.tenant_id == user_tenant_id) & (ComplianceAuditTrail.action_type == action_type)
            )
            .order_by(ComplianceAuditTrail.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return db.exec(statement).all()

    def list_by_status(
        self,
        db: Session,
        user_tenant_id: UUID,
        status: ComplianceStatus,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ComplianceAuditTrail]:
        """Filter audit entries by compliance status."""
        statement = (
            select(ComplianceAuditTrail)
            .where(
                (ComplianceAuditTrail.tenant_id == user_tenant_id) & (ComplianceAuditTrail.compliance_status == status)
            )
            .order_by(ComplianceAuditTrail.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return db.exec(statement).all()
