"""Document Category Entity - Master Data Management

Represents document classification categories that organize document types.
Supports optional hierarchy (parent-child relationships).
"""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import Column, JSON, Field, String, SQLModel

from database_core import TenantAwareBase


class DocumentCategory(TenantAwareBase, table=True):
    """Document Category Entity
    
    Organizes document types into categories for classification.
    Supports optional parent-child hierarchy for nested categorization.
    """

    __tablename__ = "document_categories"

    id: Optional[str] = Field(
        default_factory=lambda: str(uuid4()),
        primary_key=True,
        description="Category ID",
    )
    name: str = Field(
        ...,
        description="Category name",
        min_length=1,
        max_length=255,
        index=True,
    )
    description: Optional[str] = Field(
        None,
        description="Category description",
        max_length=1000,
    )
    color_code: Optional[str] = Field(
        None,
        description="Hex color for UI display (e.g., #FF5733)",
        max_length=7,
    )
    icon: Optional[str] = Field(
        None,
        description="Icon name or emoji",
        max_length=100,
    )
    parent_category_id: Optional[UUID] = Field(
        None,
        description="Parent category ID for hierarchy",
        foreign_key="document_categories.id",
        index=True,
    )
    sort_order: int = Field(
        default=0,
        description="Sort order for UI display",
    )
    is_active: bool = Field(
        default=True,
        description="Category is active and visible",
        index=True,
    )


class DocumentCategoryCreate(SQLModel):
    """Create Document Category Request"""

    name: str = Field(
        ...,
        description="Category name",
        min_length=1,
        max_length=255,
    )
    description: Optional[str] = Field(
        None,
        description="Category description",
        max_length=1000,
    )
    color_code: Optional[str] = Field(
        None,
        description="Hex color for UI display",
        max_length=7,
    )
    icon: Optional[str] = Field(
        None,
        description="Icon name or emoji",
        max_length=100,
    )
    parent_category_id: Optional[UUID] = Field(
        None,
        description="Parent category ID for nested hierarchy",
    )
    sort_order: int = Field(
        default=0,
        description="Sort order for UI",
    )


class DocumentCategoryUpdate(SQLModel):
    """Update Document Category Request"""

    name: Optional[str] = Field(
        None,
        description="Category name",
        min_length=1,
        max_length=255,
    )
    description: Optional[str] = Field(
        None,
        description="Category description",
        max_length=1000,
    )
    color_code: Optional[str] = Field(
        None,
        description="Hex color for UI display",
        max_length=7,
    )
    icon: Optional[str] = Field(
        None,
        description="Icon name or emoji",
        max_length=100,
    )
    parent_category_id: Optional[UUID] = Field(
        None,
        description="Parent category ID for nested hierarchy",
    )
    sort_order: Optional[int] = Field(
        None,
        description="Sort order for UI",
    )
    is_active: Optional[bool] = Field(
        None,
        description="Category is active",
    )


class DocumentCategoryResponse(SQLModel):
    """Document Category Response"""

    id: UUID = Field(..., description="Category ID")
    tenant_id: UUID = Field(..., description="Tenant ID")
    name: str = Field(..., description="Category name")
    description: Optional[str] = Field(None, description="Category description")
    color_code: Optional[str] = Field(None, description="Hex color")
    icon: Optional[str] = Field(None, description="Icon")
    parent_category_id: Optional[UUID] = Field(None, description="Parent category")
    sort_order: int = Field(..., description="Sort order")
    is_active: bool = Field(..., description="Is active")
    deleted_at: Optional[str] = Field(None, description="Deletion timestamp")


class DocumentCategoryNode(SQLModel):
    """Single node in category tree"""

    id: UUID = Field(..., description="Category ID")
    name: str = Field(..., description="Category name")
    description: Optional[str] = Field(None, description="Description")
    color_code: Optional[str] = Field(None, description="Color")
    icon: Optional[str] = Field(None, description="Icon")
    sort_order: int = Field(..., description="Sort order")
    children: list["DocumentCategoryNode"] = Field(
        default_factory=list,
        description="Child categories",
    )


class DocumentCategoryTreeResponse(SQLModel):
    """Nested category tree response"""

    root_categories: list[DocumentCategoryNode] = Field(
        default_factory=list,
        description="Root categories with nested children",
    )
