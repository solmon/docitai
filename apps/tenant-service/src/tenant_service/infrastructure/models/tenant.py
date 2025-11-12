"""Tenant entity model for multi-tenant application."""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from database_core.base import TenantAwareBase
from sqlmodel import Column, Field, SQLModel, String

from tenant_service.domain.enums.subscription_plan import SubscriptionPlan


class Tenant(TenantAwareBase, table=True):
    """
    Tenant entity representing a customer account in the system.

    Multi-tenant isolation:
    - Each tenant has unique tenant_id (also serves as their identifier)
    - All data is scoped to the tenant_id
    - Queries automatically filtered by tenant context

    Attributes:
        id: Primary key
        tenant_id: Tenant identifier (multi-tenant isolation)
        name: Tenant name
        display_name: Display name for UI
        description: Tenant description
        subscription_plan: Current subscription plan
        is_active: Whether tenant is active
        admin_email: Primary admin email
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    id: Optional[str] = Field(
        default_factory=lambda: str(uuid4()), primary_key=True, description="Unique tenant identifier"
    )

    # Tenant info
    name: str = Field(..., sa_column=Column(String, nullable=False, index=True), description="Tenant organization name")
    display_name: Optional[str] = Field(None, sa_column=Column(String), description="Display name for UI")
    description: Optional[str] = Field(None, sa_column=Column(String), description="Tenant description")

    # Subscription
    subscription_plan: SubscriptionPlan = Field(
        default=SubscriptionPlan.STARTER,
        sa_column=Column(String, nullable=False),
        description="Current subscription plan",
    )

    # Status
    is_active: bool = Field(
        default=True, sa_column=Column(String, nullable=False, index=True), description="Whether tenant is active"
    )

    # Contact
    admin_email: Optional[str] = Field(None, sa_column=Column(String), description="Primary admin email")

    class Config:
        """SQLModel configuration."""

        from_attributes = True


class TenantCreate(SQLModel):
    """Request model for creating a tenant."""

    name: str = Field(..., min_length=1, max_length=255)
    display_name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    subscription_plan: SubscriptionPlan = Field(default=SubscriptionPlan.STARTER)
    admin_email: Optional[str] = Field(None)


class TenantUpdate(SQLModel):
    """Request model for updating a tenant."""

    display_name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    subscription_plan: Optional[SubscriptionPlan] = None
    is_active: Optional[bool] = None
    admin_email: Optional[str] = None


class TenantResponse(SQLModel):
    """Response model for tenant data."""

    id: str
    name: str
    display_name: Optional[str]
    description: Optional[str]
    subscription_plan: SubscriptionPlan
    is_active: bool
    admin_email: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
