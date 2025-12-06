"""CQRS handlers for retention policy management."""

import logging
from uuid import UUID

from sqlmodel import Session

from tenant_service.domain.services.retention_policy_service import RetentionPolicyService
from tenant_service.infrastructure.models.retention_policy import (
    RetentionPolicyCreate,
    RetentionPolicyUpdate,
)

logger = logging.getLogger(__name__)


class CreateRetentionPolicyCommand:
    """Command to create retention policy."""

    def __init__(
        self,
        user_tenant_id: UUID,
        user_id: UUID,
        data: RetentionPolicyCreate,
    ):
        self.user_tenant_id = user_tenant_id
        self.user_id = user_id
        self.data = data


class UpdateRetentionPolicyCommand:
    """Command to update retention policy."""

    def __init__(
        self,
        user_tenant_id: UUID,
        user_id: UUID,
        policy_id: UUID,
        data: RetentionPolicyUpdate,
    ):
        self.user_tenant_id = user_tenant_id
        self.user_id = user_id
        self.policy_id = policy_id
        self.data = data


class DeleteRetentionPolicyCommand:
    """Command to delete retention policy."""

    def __init__(
        self,
        user_tenant_id: UUID,
        user_id: UUID,
        policy_id: UUID,
    ):
        self.user_tenant_id = user_tenant_id
        self.user_id = user_id
        self.policy_id = policy_id


class CreateRetentionPolicyHandler:
    """Handle policy creation command."""

    def __init__(self, service: RetentionPolicyService):
        self.service = service

    def handle(self, db: Session, command: CreateRetentionPolicyCommand):
        """Execute create policy command."""
        logger.info(f"Creating policy '{command.data.name}' for tenant {command.user_tenant_id}")
        policy = self.service.create_policy(
            db=db,
            user_tenant_id=command.user_tenant_id,
            user_id=command.user_id,
            data=command.data,
        )
        logger.info(f"Policy {policy.id} created successfully")
        return policy


class UpdateRetentionPolicyHandler:
    """Handle policy update command."""

    def __init__(self, service: RetentionPolicyService):
        self.service = service

    def handle(self, db: Session, command: UpdateRetentionPolicyCommand):
        """Execute update policy command."""
        logger.info(f"Updating policy {command.policy_id}")
        policy = self.service.update_policy(
            db=db,
            user_tenant_id=command.user_tenant_id,
            user_id=command.user_id,
            policy_id=command.policy_id,
            data=command.data,
        )
        logger.info(f"Policy {command.policy_id} updated successfully")
        return policy


class DeleteRetentionPolicyHandler:
    """Handle policy deletion command."""

    def __init__(self, service: RetentionPolicyService):
        self.service = service

    def handle(self, db: Session, command: DeleteRetentionPolicyCommand):
        """Execute delete policy command."""
        logger.info(f"Deleting policy {command.policy_id}")
        self.service.delete_policy(
            db=db,
            user_tenant_id=command.user_tenant_id,
            user_id=command.user_id,
            policy_id=command.policy_id,
        )
        logger.info(f"Policy {command.policy_id} deleted successfully")
