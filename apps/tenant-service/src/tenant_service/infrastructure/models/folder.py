"""Folder models for hierarchical document organization."""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field
from sqlmodel import Field as SQLField
from sqlmodel import SQLModel, Column, String

from database_core.base import TenantAwareBase


class Folder(TenantAwareBase, table=True):
    """Hierarchical folder entity for document organization."""

    __tablename__ = "folders"

    id: Optional[str] = SQLField(default_factory=lambda: str(uuid4()), primary_key=True)
    tenant_id: str = SQLField(..., index=True)
    created_at: datetime = SQLField(default_factory=datetime.utcnow)
    updated_at: datetime = SQLField(default_factory=datetime.utcnow)
    name: str = SQLField(index=True, min_length=1, max_length=255)
    parent_id: Optional[UUID] = SQLField(default=None, foreign_key="folders.id", index=True)
    path: str = SQLField(unique=False, index=True, max_length=500)
    description: Optional[str] = SQLField(default=None, max_length=1000)
    owner_id: UUID
    is_archived: bool = SQLField(default=False, index=True)
    deleted_at: Optional[datetime] = SQLField(default=None, index=True)
    child_count: int = SQLField(default=0)
    depth: int = SQLField(default=0, ge=0, le=20)


class FolderCreate(BaseModel):
    """Request model for creating folder."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    parent_id: Optional[UUID] = None


class FolderUpdate(BaseModel):
    """Request model for updating folder."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)


class FolderMove(BaseModel):
    """Request model for moving folder."""

    new_parent_id: Optional[UUID] = None


class FolderResponse(BaseModel):
    """Response model for folder."""

    id: UUID
    tenant_id: UUID
    name: str
    parent_id: Optional[UUID]
    path: str
    description: Optional[str]
    owner_id: UUID
    is_archived: bool
    child_count: int
    depth: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class FolderTreeResponse(BaseModel):
    """Response model for folder with tree structure."""

    id: UUID
    name: str
    path: str
    description: Optional[str]
    owner_id: UUID
    is_archived: bool
    child_count: int
    depth: int
    children: list["FolderTreeResponse"] = []

    model_config = {"from_attributes": True}


class BreadcrumbItem(BaseModel):
    """Single item in breadcrumb path."""

    id: UUID
    name: str
    path: str


class BreadcrumbResponse(BaseModel):
    """Breadcrumb navigation response."""

    current: BreadcrumbItem
    parents: list[BreadcrumbItem]
    full_path: str
