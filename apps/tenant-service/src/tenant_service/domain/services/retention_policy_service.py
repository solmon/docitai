"""Retention policy domain service with business logic."""

from datetime import datetime, timedelta
from uuid import UUID

from sqlmodel import Session

from tenant_service.domain.enums.retention_types import (
    AppliesTo,
    AuditActionType,
    ComplianceStatus,
)
from tenant_service.exceptions import (
    ValidationError,
)
from tenant_service.infrastructure.models.retention_policy import (
    RetentionPolicyCreate,
    RetentionPolicyUpdate,
)
from tenant_service.infrastructure.repositories.compliance_audit_repository import (
    ComplianceAuditRepository,
)
from tenant_service.infrastructure.repositories.retention_policy_repository import (
    RetentionPolicyRepository,
)


class RetentionPolicyService:
    """Business logic for retention policies."""

    def __init__(
        self,
        policy_repository: RetentionPolicyRepository,
        audit_repository: ComplianceAuditRepository,
    ):
        self.policy_repo = policy_repository
        self.audit_repo = audit_repository

    def create_policy(
        self,
        db: Session,
        user_tenant_id: UUID,
        user_id: UUID,
        data: RetentionPolicyCreate,
    ):
        """Create retention policy with validation."""
        # Validate configuration based on applies_to
        if data.applies_to != AppliesTo.ALL and not data.filter_config:
            raise ValidationError("filter_config required when applies_to is not ALL")

        policy = self.policy_repo.create(
            db=db,
            user_tenant_id=user_tenant_id,
            name=data.name,
            description=data.description,
            resource_type=data.resource_type.value,
            retention_type=data.retention_type.value,
            retention_days=data.retention_days,
            applies_to=data.applies_to.value,
            filter_config=data.filter_config or {},
            created_by=user_id,
            is_active=data.is_active,
        )

        # Log creation
        self.audit_repo.log_action(
            db=db,
            user_tenant_id=user_tenant_id,
            action_type=AuditActionType.POLICY_CREATED,
            resource_type="retention_policy",
            resource_id=policy.id,
            changed_by=user_id,
            new_value=policy.model_dump(),
            reason=f"Created retention policy: {data.name}",
        )

        return policy

    def get_policy(self, db: Session, user_tenant_id: UUID, policy_id: UUID):
        """Get policy with tenant verification."""
        return self.policy_repo.get_by_id(db, user_tenant_id, policy_id)

    def list_policies(
        self,
        db: Session,
        user_tenant_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ):
        """List policies for tenant."""
        return self.policy_repo.list_by_tenant(db, user_tenant_id, limit=limit, offset=offset)

    def update_policy(
        self,
        db: Session,
        user_tenant_id: UUID,
        user_id: UUID,
        policy_id: UUID,
        data: RetentionPolicyUpdate,
    ):
        """Update policy with change tracking."""
        old_policy = self.get_policy(db, user_tenant_id, policy_id)

        update_dict = data.model_dump(exclude_unset=True)
        if not update_dict:
            return old_policy

        policy = self.policy_repo.update(db, user_tenant_id, policy_id, **update_dict)

        # Log update
        self.audit_repo.log_action(
            db=db,
            user_tenant_id=user_tenant_id,
            action_type=AuditActionType.POLICY_UPDATED,
            resource_type="retention_policy",
            resource_id=policy_id,
            changed_by=user_id,
            old_value={"changed_fields": list(update_dict.keys())},
            new_value=policy.model_dump(),
            reason="Policy updated",
        )

        return policy

    def delete_policy(
        self,
        db: Session,
        user_tenant_id: UUID,
        user_id: UUID,
        policy_id: UUID,
    ) -> None:
        """Delete policy with audit trail."""
        policy = self.get_policy(db, user_tenant_id, policy_id)

        self.policy_repo.delete(db, user_tenant_id, policy_id)

        # Log deletion
        self.audit_repo.log_action(
            db=db,
            user_tenant_id=user_tenant_id,
            action_type=AuditActionType.POLICY_DELETED,
            resource_type="retention_policy",
            resource_id=policy_id,
            changed_by=user_id,
            old_value=policy.model_dump(),
            reason="Policy deleted",
        )

    def calculate_retention_date(self, policy_created_at: datetime, retention_days: int) -> datetime:
        """Calculate when retention period expires."""
        return policy_created_at + timedelta(days=retention_days)

    def should_apply_policy(self, resource_date: datetime, retention_days: int) -> bool:
        """Check if retention period has passed for resource."""
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        return resource_date <= cutoff_date

    def execute_policy(
        self,
        db: Session,
        user_tenant_id: UUID,
        user_id: UUID,
        policy_id: UUID,
    ):
        """Execute retention policy (trigger deletion/archival)."""
        policy = self.get_policy(db, user_tenant_id, policy_id)

        if not policy.is_active:
            raise ValidationError("Cannot execute inactive policy")

        # In real implementation, this would:
        # 1. Find resources matching policy criteria
        # 2. Check retention period has passed
        # 3. Perform deletion or archival
        # 4. Log each action to audit trail

        # Increment execution count
        executed_count = self.policy_repo.increment_execution_count(db, user_tenant_id, policy_id)

        # Log execution
        self.audit_repo.log_action(
            db=db,
            user_tenant_id=user_tenant_id,
            action_type=AuditActionType.POLICY_EXECUTED,
            resource_type="retention_policy",
            resource_id=policy_id,
            changed_by=user_id,
            new_value={"executed_count": executed_count},
            reason=f"Policy executed (count: {executed_count})",
            compliance_status=ComplianceStatus.SUCCESS,
        )

        return {
            "policy_id": policy_id,
            "executed_count": executed_count,
            "status": "success",
        }
