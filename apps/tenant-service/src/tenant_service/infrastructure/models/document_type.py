"""Document Type Entity - Master Data Management

Represents specific document types with custom attributes and constraints.
Templates for documents that can be classified under categories.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional
from uuid import UUID, uuid4

from sqlmodel import Column, JSON, Field, SQLModel

from database_core import TenantAwareBase

if TYPE_CHECKING:
    from tenant_service.infrastructure.models.document_category import DocumentCategoryResponse


class DocumentType(TenantAwareBase, table=True):
    """Document Type Entity

    Template for a specific document type with custom attributes,
    file constraints, and retention settings.
    """

    __tablename__ = "document_types"

    id: Optional[str] = Field(
        default_factory=lambda: str(uuid4()),
        primary_key=True,
        description="Document type ID",
    )
    tenant_id: str = Field(
        ...,
        index=True,
        description="Tenant identifier for multi-tenant isolation",
    )
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Record creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    name: str = Field(
        ...,
        description="Document type name",
        min_length=1,
        max_length=255,
        index=True,
    )
    description: Optional[str] = Field(
        None,
        description="Document type description",
        max_length=1000,
    )
    category_id: UUID = Field(
        ...,
        description="Category ID (FK)",
        foreign_key="document_categories.id",
        index=True,
    )
    file_extensions: list[str] = Field(
        default_factory=list,
        description="Allowed file extensions (e.g., ['.pdf', '.docx'])",
        sa_column=Column(JSON),
    )
    max_file_size: int = Field(
        default=10485760,  # 10MB default
        description="Maximum file size in bytes",
        ge=0,
        le=5368709120,  # 5GB max
    )
    retention_days: Optional[int] = Field(
        None,
        description="Default retention period in days",
        ge=1,
        le=36500,  # 100 years max
    )
    custom_attributes: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Custom attributes schema as JSON",
        sa_column=Column(JSON),
    )
    is_active: bool = Field(
        default=True,
        description="Document type is active",
        index=True,
    )

    # Indexes handled via field index=True


class DocumentTypeCreate(SQLModel):
    """Create Document Type Request"""

    name: str = Field(
        ...,
        description="Document type name",
        min_length=1,
        max_length=255,
    )
    description: Optional[str] = Field(
        None,
        description="Document type description",
        max_length=1000,
    )
    category_id: UUID = Field(
        ...,
        description="Category ID",
    )
    file_extensions: list[str] = Field(
        default_factory=list,
        description="Allowed file extensions",
    )
    max_file_size: int = Field(
        default=10485760,
        description="Maximum file size in bytes",
        ge=0,
        le=5368709120,
    )
    retention_days: Optional[int] = Field(
        None,
        description="Default retention period in days",
        ge=1,
        le=36500,
    )
    custom_attributes: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Custom attributes schema",
    )


class DocumentTypeUpdate(SQLModel):
    """Update Document Type Request"""

    name: Optional[str] = Field(
        None,
        description="Document type name",
        min_length=1,
        max_length=255,
    )
    description: Optional[str] = Field(
        None,
        description="Document type description",
        max_length=1000,
    )
    category_id: Optional[UUID] = Field(
        None,
        description="Category ID",
    )
    file_extensions: Optional[list[str]] = Field(
        None,
        description="Allowed file extensions",
    )
    max_file_size: Optional[int] = Field(
        None,
        description="Maximum file size in bytes",
        ge=0,
        le=5368709120,
    )
    retention_days: Optional[int] = Field(
        None,
        description="Default retention period in days",
        ge=1,
        le=36500,
    )
    custom_attributes: Optional[list[dict[str, Any]]] = Field(
        None,
        description="Custom attributes schema",
    )
    is_active: Optional[bool] = Field(
        None,
        description="Document type is active",
    )


class DocumentTypeResponse(SQLModel):
    """Document Type Response"""

    id: UUID = Field(..., description="Type ID")
    tenant_id: UUID = Field(..., description="Tenant ID")
    name: str = Field(..., description="Type name")
    description: Optional[str] = Field(None, description="Type description")
    category_id: UUID = Field(..., description="Category ID")
    file_extensions: list[str] = Field(..., description="Allowed extensions")
    max_file_size: int = Field(..., description="Max file size")
    retention_days: Optional[int] = Field(None, description="Retention period")
    custom_attributes: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Custom attributes",
    )
    is_active: bool = Field(..., description="Is active")
    deleted_at: Optional[str] = Field(None, description="Deletion timestamp")


class DocumentTypeWithCategoryResponse(SQLModel):
    """Document Type with nested category"""

    id: UUID = Field(..., description="Type ID")
    tenant_id: UUID = Field(..., description="Tenant ID")
    name: str = Field(..., description="Type name")
    description: Optional[str] = Field(None, description="Type description")
    category: "DocumentCategoryResponse" = Field(..., description="Category")
    file_extensions: list[str] = Field(..., description="Allowed extensions")
    max_file_size: int = Field(..., description="Max file size")
    retention_days: Optional[int] = Field(None, description="Retention period")
    custom_attributes: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Custom attributes",
    )
    is_active: bool = Field(..., description="Is active")
    deleted_at: Optional[str] = Field(None, description="Deletion timestamp")


class CustomAttributeSchema(SQLModel):
    """Schema for document custom attributes"""

    name: str = Field(
        ...,
        description="Attribute name",
        min_length=1,
        max_length=100,
    )
    attribute_type: str = Field(
        ...,
        description="Attribute type",
    )
    required: bool = Field(
        default=False,
        description="Attribute is required",
    )
    default_value: Optional[Any] = Field(
        None,
        description="Default value",
    )
    validation_rules: dict[str, Any] = Field(
        default_factory=dict,
        description="Validation rules",
    )
    enum_values: Optional[list[Any]] = Field(
        None,
        description="Enum values for enum type",
    )


class AttributeSchemaResponse(SQLModel):
    """Response with attribute schema"""

    attributes: list[CustomAttributeSchema] = Field(
        default_factory=list,
        description="Custom attributes schema",
    )
