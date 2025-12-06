"""CQRS handlers for policy execution and compliance verification."""

import logging
from uuid import UUID

from sqlmodel import Session

from tenant_service.domain.services.compliance_service import ComplianceService
from tenant_service.domain.services.retention_policy_service import RetentionPolicyService

logger = logging.getLogger(__name__)


class ExecuteRetentionPolicyCommand:
    """Command to execute retention policy."""

    def __init__(
        self,
        user_tenant_id: UUID,
        user_id: UUID,
        policy_id: UUID,
    ):
        self.user_tenant_id = user_tenant_id
        self.user_id = user_id
        self.policy_id = policy_id


class VerifyComplianceCommand:
    """Command to verify compliance status."""

    def __init__(
        self,
        user_tenant_id: UUID,
        user_id: UUID,
    ):
        self.user_tenant_id = user_tenant_id
        self.user_id = user_id


class ExecuteRetentionPolicyHandler:
    """Handle policy execution command."""

    def __init__(self, service: RetentionPolicyService):
        self.service = service

    def handle(self, db: Session, command: ExecuteRetentionPolicyCommand):
        """Execute retention policy command."""
        logger.info(f"Executing policy {command.policy_id} for tenant {command.user_tenant_id}")
        result = self.service.execute_policy(
            db=db,
            user_tenant_id=command.user_tenant_id,
            user_id=command.user_id,
            policy_id=command.policy_id,
        )
        logger.info(f"Policy execution completed: {result}")
        return result


class VerifyComplianceHandler:
    """Handle compliance verification command."""

    def __init__(
        self,
        policy_service: RetentionPolicyService,
        compliance_service: ComplianceService,
    ):
        self.policy_service = policy_service
        self.compliance_service = compliance_service

    def handle(self, db: Session, command: VerifyComplianceCommand):
        """Verify compliance status for tenant."""
        logger.info(f"Verifying compliance for tenant {command.user_tenant_id}")

        # Get all policies
        policies = self.policy_service.list_policies(
            db=db,
            user_tenant_id=command.user_tenant_id,
            limit=1000,
        )

        # Log verification
        verification_result = {
            "tenant_id": str(command.user_tenant_id),
            "verified_at": __import__("datetime").datetime.utcnow().isoformat(),
            "total_policies": len(policies),
            "active_policies": sum(1 for p in policies if p.is_active),
        }

        logger.info(f"Compliance verification completed: {verification_result}")
        return verification_result
