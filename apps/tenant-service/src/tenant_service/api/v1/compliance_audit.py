"""REST API endpoints for compliance audit trail."""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

from tenant_service.api.dependencies import get_current_user, get_db
from tenant_service.domain.enums.retention_types import AuditActionType, ComplianceStatus
from tenant_service.domain.services.compliance_service import ComplianceService
from tenant_service.infrastructure.models.compliance_audit_trail import (
    ComplianceAuditTrailResponse,
)
from tenant_service.infrastructure.repositories.compliance_audit_repository import (
    ComplianceAuditRepository,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/audit", tags=["Compliance Audit"])


@router.get(
    "/{resource_type}/{resource_id}",
    response_model=list[ComplianceAuditTrailResponse],
)
async def get_resource_audit_trail(
    resource_type: str,
    resource_id: UUID,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Get audit trail for specific resource."""
    try:
        audit_repo = ComplianceAuditRepository()
        service = ComplianceService(audit_repo)
        entries = service.get_resource_audit_trail(
            db=db,
            user_tenant_id=user.tenant_id,
            resource_type=resource_type,
            resource_id=resource_id,
            limit=limit,
            offset=offset,
        )
        return entries
    except Exception as e:
        logger.error(f"Error fetching resource audit trail: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("", response_model=list[ComplianceAuditTrailResponse])
async def get_tenant_audit_trail(
    action_type: Optional[AuditActionType] = Query(None),
    status_filter: Optional[ComplianceStatus] = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Get audit trail for tenant with optional filters."""
    try:
        audit_repo = ComplianceAuditRepository()
        service = ComplianceService(audit_repo)

        if action_type:
            entries = service.get_audit_by_action(
                db=db,
                user_tenant_id=user.tenant_id,
                action_type=action_type,
                limit=limit,
                offset=offset,
            )
        elif status_filter:
            entries = service.get_audit_by_status(
                db=db,
                user_tenant_id=user.tenant_id,
                status=status_filter,
                limit=limit,
                offset=offset,
            )
        else:
            entries = service.get_tenant_audit_trail(
                db=db,
                user_tenant_id=user.tenant_id,
                limit=limit,
                offset=offset,
            )
        return entries
    except Exception as e:
        logger.error(f"Error fetching audit trail: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/export", response_model=dict)
async def export_audit_report(
    format: str = Query("json", pattern="^(json|csv)$"),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Export audit report for compliance."""
    try:
        audit_repo = ComplianceAuditRepository()
        service = ComplianceService(audit_repo)
        report = service.export_audit_report(
            db=db,
            user_tenant_id=user.tenant_id,
            format=format,
        )
        return report
    except Exception as e:
        logger.error(f"Error exporting audit report: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")
