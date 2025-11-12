"""Tenant settings value object."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class TenantSettings(BaseModel):
    """
    Value object for tenant configuration and settings.

    Immutable data object representing tenant settings configuration.
    """

    name: str = Field(..., min_length=1, max_length=255, description="Tenant name")
    display_name: Optional[str] = Field(None, max_length=255, description="Display name for UI")
    description: Optional[str] = Field(None, max_length=1000, description="Tenant description")

    # Contact information
    contact_email: Optional[EmailStr] = Field(None, description="Primary contact email")
    contact_phone: Optional[str] = Field(None, max_length=20, description="Primary contact phone")

    # Configuration
    max_users: int = Field(default=10, ge=1, description="Maximum number of users")
    max_storage_gb: int = Field(default=100, ge=1, description="Maximum storage in GB")

    # Features
    features: dict[str, bool] = Field(
        default_factory=lambda: {
            "folder_management": True,
            "compliance_policies": True,
            "custom_categories": True,
        },
        description="Enabled features for this tenant",
    )

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True
