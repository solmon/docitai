"""Retention policy repository with multi-tenant isolation."""

from typing import Optional
from uuid import UUID

from sqlmodel import Session, select

from tenant_service.exceptions import ResourceNotFoundError, TenantIsolationViolationError
from tenant_service.infrastructure.models.retention_policy import RetentionPolicy


class RetentionPolicyRepository:
    """Repository for retention policy data access with tenant isolation."""

    def create(
        self,
        db: Session,
        user_tenant_id: UUID,
        name: str,
        description: Optional[str],
        resource_type: str,
        retention_type: str,
        retention_days: int,
        applies_to: str,
        filter_config: dict,
        created_by: UUID,
        is_active: bool = True,
    ) -> RetentionPolicy:
        """Create new retention policy."""
        policy = RetentionPolicy(
            tenant_id=user_tenant_id,
            name=name,
            description=description,
            resource_type=resource_type,
            retention_type=retention_type,
            retention_days=retention_days,
            applies_to=applies_to,
            filter_config=filter_config,
            created_by=created_by,
            is_active=is_active,
        )
        db.add(policy)
        db.commit()
        db.refresh(policy)
        return policy

    def get_by_id(self, db: Session, user_tenant_id: UUID, policy_id: UUID) -> RetentionPolicy:
        """Get policy by ID with tenant verification."""
        statement = select(RetentionPolicy).where(
            (RetentionPolicy.id == policy_id) & (RetentionPolicy.tenant_id == user_tenant_id)
        )
        policy = db.exec(statement).first()
        if not policy:
            raise ResourceNotFoundError(f"Retention policy {policy_id} not found")
        return policy

    def list_by_tenant(
        self, db: Session, user_tenant_id: UUID, limit: int = 50, offset: int = 0
    ) -> list[RetentionPolicy]:
        """List all policies for tenant."""
        statement = (
            select(RetentionPolicy)
            .where(RetentionPolicy.tenant_id == user_tenant_id)
            .order_by(RetentionPolicy.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return db.exec(statement).all()

    def list_active(self, db: Session, user_tenant_id: UUID) -> list[RetentionPolicy]:
        """List active policies for scheduler execution."""
        statement = select(RetentionPolicy).where(
            (RetentionPolicy.tenant_id == user_tenant_id)
            & (RetentionPolicy.is_active.is_(True))
        )
        return db.exec(statement).all()

    def update(
        self,
        db: Session,
        user_tenant_id: UUID,
        policy_id: UUID,
        **kwargs,
    ) -> RetentionPolicy:
        """Update policy fields."""
        policy = self.get_by_id(db, user_tenant_id, policy_id)

        # Only allow updates to specific fields
        allowed_fields = {
            "name",
            "description",
            "retention_days",
            "applies_to",
            "filter_config",
            "is_active",
        }
        for field, value in kwargs.items():
            if field in allowed_fields and value is not None:
                setattr(policy, field, value)

        db.add(policy)
        db.commit()
        db.refresh(policy)
        return policy

    def delete(self, db: Session, user_tenant_id: UUID, policy_id: UUID) -> None:
        """Soft delete retention policy."""
        policy = self.get_by_id(db, user_tenant_id, policy_id)
        policy.is_active = False
        db.add(policy)
        db.commit()

    def increment_execution_count(
        self, db: Session, user_tenant_id: UUID, policy_id: UUID
    ) -> int:
        """Increment execution count for tracking."""
        policy = self.get_by_id(db, user_tenant_id, policy_id)
        policy.executed_count += 1
        db.add(policy)
        db.commit()
        db.refresh(policy)
        return policy.executed_count
