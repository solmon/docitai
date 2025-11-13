"""Compliance audit and reporting service."""

from typing import Optional
from uuid import UUID

from sqlmodel import Session

from tenant_service.domain.enums.retention_types import AuditActionType, ComplianceStatus
from tenant_service.infrastructure.repositories.compliance_audit_repository import (
    ComplianceAuditRepository,
)


class ComplianceService:
    """Business logic for compliance auditing and reporting."""

    def __init__(self, audit_repository: ComplianceAuditRepository):
        self.audit_repo = audit_repository

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
    ):
        """Log compliance action to immutable audit trail."""
        return self.audit_repo.log_action(
            db=db,
            user_tenant_id=user_tenant_id,
            action_type=action_type,
            resource_type=resource_type,
            resource_id=resource_id,
            changed_by=changed_by,
            old_value=old_value,
            new_value=new_value,
            reason=reason,
            compliance_status=compliance_status,
        )

    def get_resource_audit_trail(
        self,
        db: Session,
        user_tenant_id: UUID,
        resource_type: str,
        resource_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ):
        """Get complete audit history for resource."""
        return self.audit_repo.list_by_resource(
            db=db,
            user_tenant_id=user_tenant_id,
            resource_type=resource_type,
            resource_id=resource_id,
            limit=limit,
            offset=offset,
        )

    def get_tenant_audit_trail(
        self,
        db: Session,
        user_tenant_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ):
        """Get all audit entries for tenant."""
        return self.audit_repo.list_by_tenant(
            db=db,
            user_tenant_id=user_tenant_id,
            limit=limit,
            offset=offset,
        )

    def get_audit_by_action(
        self,
        db: Session,
        user_tenant_id: UUID,
        action_type: AuditActionType,
        limit: int = 50,
        offset: int = 0,
    ):
        """Get audit entries by action type."""
        return self.audit_repo.list_by_action_type(
            db=db,
            user_tenant_id=user_tenant_id,
            action_type=action_type,
            limit=limit,
            offset=offset,
        )

    def get_audit_by_status(
        self,
        db: Session,
        user_tenant_id: UUID,
        status: ComplianceStatus,
        limit: int = 50,
        offset: int = 0,
    ):
        """Get audit entries by compliance status."""
        return self.audit_repo.list_by_status(
            db=db,
            user_tenant_id=user_tenant_id,
            status=status,
            limit=limit,
            offset=offset,
        )

    def export_audit_report(
        self,
        db: Session,
        user_tenant_id: UUID,
        format: str = "json",
    ) -> dict:
        """Export audit trail for compliance reporting."""
        # Get all audit entries for tenant
        audit_entries = self.audit_repo.list_by_tenant(
            db=db,
            user_tenant_id=user_tenant_id,
            limit=10000,  # Large limit for export
            offset=0,
        )

        if format == "json":
            return {
                "tenant_id": str(user_tenant_id),
                "total_entries": len(audit_entries),
                "entries": [
                    {
                        "id": str(entry.id),
                        "action_type": entry.action_type.value,
                        "resource_type": entry.resource_type,
                        "resource_id": str(entry.resource_id),
                        "changed_by": str(entry.changed_by),
                        "reason": entry.reason,
                        "compliance_status": entry.compliance_status.value,
                        "created_at": entry.created_at.isoformat(),
                    }
                    for entry in audit_entries
                ],
            }

        # CSV format
        csv_rows = [
            "id,action_type,resource_type,resource_id,changed_by,reason,status,created_at"
        ]
        for entry in audit_entries:
            csv_rows.append(
                f"{entry.id},{entry.action_type.value},{entry.resource_type},"
                f"{entry.resource_id},{entry.changed_by},{entry.reason or ''},"
                f"{entry.compliance_status.value},{entry.created_at.isoformat()}"
            )

        return {
            "format": "csv",
            "data": "\n".join(csv_rows),
        }
