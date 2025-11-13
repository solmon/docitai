"""REST API endpoints for retention policy management."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

from tenant_service.api.dependencies import get_current_user, get_db
from tenant_service.application.handlers.retention_policy_handler import (
    CreateRetentionPolicyCommand,
    CreateRetentionPolicyHandler,
    DeleteRetentionPolicyCommand,
    DeleteRetentionPolicyHandler,
    UpdateRetentionPolicyCommand,
    UpdateRetentionPolicyHandler,
)
from tenant_service.application.handlers.policy_execution_handler import (
    ExecuteRetentionPolicyCommand,
    ExecuteRetentionPolicyHandler,
)
from tenant_service.domain.services.retention_policy_service import RetentionPolicyService
from tenant_service.domain.services.compliance_service import ComplianceService
from tenant_service.exceptions import ResourceNotFoundError, TenantServiceException
from tenant_service.infrastructure.models.retention_policy import (
    RetentionPolicyCreate,
    RetentionPolicyResponse,
    RetentionPolicyUpdate,
)
from tenant_service.infrastructure.repositories.retention_policy_repository import (
    RetentionPolicyRepository,
)
from tenant_service.infrastructure.repositories.compliance_audit_repository import (
    ComplianceAuditRepository,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/policies", tags=["Retention Policies"])


@router.post(
    "",
    response_model=RetentionPolicyResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_policy(
    data: RetentionPolicyCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Create new retention policy."""
    try:
        policy_repo = RetentionPolicyRepository()
        audit_repo = ComplianceAuditRepository()
        service = RetentionPolicyService(policy_repo, audit_repo)
        handler = CreateRetentionPolicyHandler(service)

        command = CreateRetentionPolicyCommand(
            user_tenant_id=user.tenant_id,
            user_id=user.id,
            data=data,
        )
        policy = handler.handle(db, command)
        return policy
    except TenantServiceException as e:
        logger.error(f"Failed to create policy: {e}")
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error creating policy: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error"
        )


@router.get("/{policy_id}", response_model=RetentionPolicyResponse)
async def get_policy(
    policy_id: UUID,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Get retention policy by ID."""
    try:
        policy_repo = RetentionPolicyRepository()
        audit_repo = ComplianceAuditRepository()
        service = RetentionPolicyService(policy_repo, audit_repo)
        policy = service.get_policy(db, user.tenant_id, policy_id)
        return policy
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error fetching policy: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error"
        )


@router.get("", response_model=list[RetentionPolicyResponse])
async def list_policies(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """List retention policies for tenant."""
    try:
        policy_repo = RetentionPolicyRepository()
        audit_repo = ComplianceAuditRepository()
        service = RetentionPolicyService(policy_repo, audit_repo)
        policies = service.list_policies(db, user.tenant_id, limit=limit, offset=offset)
        return policies
    except Exception as e:
        logger.error(f"Error listing policies: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error"
        )


@router.put("/{policy_id}", response_model=RetentionPolicyResponse)
async def update_policy(
    policy_id: UUID,
    data: RetentionPolicyUpdate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Update retention policy."""
    try:
        policy_repo = RetentionPolicyRepository()
        audit_repo = ComplianceAuditRepository()
        service = RetentionPolicyService(policy_repo, audit_repo)
        handler = UpdateRetentionPolicyHandler(service)

        command = UpdateRetentionPolicyCommand(
            user_tenant_id=user.tenant_id,
            user_id=user.id,
            policy_id=policy_id,
            data=data,
        )
        policy = handler.handle(db, command)
        return policy
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except TenantServiceException as e:
        logger.error(f"Failed to update policy: {e}")
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error updating policy: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error"
        )


@router.delete("/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_policy(
    policy_id: UUID,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Delete retention policy."""
    try:
        policy_repo = RetentionPolicyRepository()
        audit_repo = ComplianceAuditRepository()
        service = RetentionPolicyService(policy_repo, audit_repo)
        handler = DeleteRetentionPolicyHandler(service)

        command = DeleteRetentionPolicyCommand(
            user_tenant_id=user.tenant_id,
            user_id=user.id,
            policy_id=policy_id,
        )
        handler.handle(db, command)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting policy: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error"
        )


@router.post(
    "/{policy_id}/execute",
    response_model=dict,
    status_code=status.HTTP_200_OK,
)
async def execute_policy(
    policy_id: UUID,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Execute retention policy manually."""
    try:
        policy_repo = RetentionPolicyRepository()
        audit_repo = ComplianceAuditRepository()
        service = RetentionPolicyService(policy_repo, audit_repo)
        handler = ExecuteRetentionPolicyHandler(service)

        command = ExecuteRetentionPolicyCommand(
            user_tenant_id=user.tenant_id,
            user_id=user.id,
            policy_id=policy_id,
        )
        result = handler.handle(db, command)
        return result
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except TenantServiceException as e:
        logger.error(f"Failed to execute policy: {e}")
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error executing policy: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error"
        )
