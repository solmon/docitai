"""Master Data CQRS Handlers - Commands and Event Handlers

Implements command handlers for master data operations.
"""

from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel
from sqlmodel import Session

from tenant_service.domain.services.master_data_service import MasterDataService
from tenant_service.infrastructure.models.document_category import (
    DocumentCategoryResponse,
)
from tenant_service.infrastructure.models.document_type import DocumentTypeResponse


# ============= Category Commands =============


class CreateCategoryCommand(BaseModel):
    """Create category command"""

    tenant_id: UUID
    name: str
    description: Optional[str] = None
    color_code: Optional[str] = None
    icon: Optional[str] = None
    parent_category_id: Optional[UUID] = None
    sort_order: int = 0


class CreateCategoryHandler:
    """Handler for creating categories"""

    def __init__(self, db: Session):
        self.service = MasterDataService(db)

    async def handle(self, cmd: CreateCategoryCommand) -> DocumentCategoryResponse:
        """Create a new category

        Args:
            cmd: Create command

        Returns:
            Created category response
        """
        category = await self.service.create_category(
            tenant_id=cmd.tenant_id,
            name=cmd.name,
            description=cmd.description,
            color_code=cmd.color_code,
            icon=cmd.icon,
            parent_category_id=cmd.parent_category_id,
            sort_order=cmd.sort_order,
        )

        return DocumentCategoryResponse(
            id=category.id,
            tenant_id=category.tenant_id,
            name=category.name,
            description=category.description,
            color_code=category.color_code,
            icon=category.icon,
            parent_category_id=category.parent_category_id,
            sort_order=category.sort_order,
            is_active=category.is_active,
            deleted_at=category.deleted_at.isoformat() if category.deleted_at else None,
        )


class UpdateCategoryCommand(BaseModel):
    """Update category command"""

    tenant_id: UUID
    category_id: UUID
    name: Optional[str] = None
    description: Optional[str] = None
    color_code: Optional[str] = None
    icon: Optional[str] = None
    parent_category_id: Optional[UUID] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class UpdateCategoryHandler:
    """Handler for updating categories"""

    def __init__(self, db: Session):
        self.service = MasterDataService(db)

    async def handle(self, cmd: UpdateCategoryCommand) -> DocumentCategoryResponse:
        """Update an existing category

        Args:
            cmd: Update command

        Returns:
            Updated category response
        """
        category = await self.service.update_category(
            category_id=cmd.category_id,
            tenant_id=cmd.tenant_id,
            name=cmd.name,
            description=cmd.description,
            color_code=cmd.color_code,
            icon=cmd.icon,
            parent_category_id=cmd.parent_category_id,
            sort_order=cmd.sort_order,
            is_active=cmd.is_active,
        )

        return DocumentCategoryResponse(
            id=category.id,
            tenant_id=category.tenant_id,
            name=category.name,
            description=category.description,
            color_code=category.color_code,
            icon=category.icon,
            parent_category_id=category.parent_category_id,
            sort_order=category.sort_order,
            is_active=category.is_active,
            deleted_at=category.deleted_at.isoformat() if category.deleted_at else None,
        )


class DeleteCategoryCommand(BaseModel):
    """Delete category command"""

    tenant_id: UUID
    category_id: UUID


class DeleteCategoryHandler:
    """Handler for deleting categories"""

    def __init__(self, db: Session):
        self.service = MasterDataService(db)

    async def handle(self, cmd: DeleteCategoryCommand) -> bool:
        """Delete a category (soft delete)

        Args:
            cmd: Delete command

        Returns:
            True if deleted
        """
        return await self.service.delete_category(cmd.category_id, cmd.tenant_id)


class RestoreCategoryCommand(BaseModel):
    """Restore category command"""

    tenant_id: UUID
    category_id: UUID


class RestoreCategoryHandler:
    """Handler for restoring deleted categories"""

    def __init__(self, db: Session):
        self.service = MasterDataService(db)

    async def handle(self, cmd: RestoreCategoryCommand) -> bool:
        """Restore a soft-deleted category

        Args:
            cmd: Restore command

        Returns:
            True if restored
        """
        return await self.service.restore_category(cmd.category_id, cmd.tenant_id)


# ============= Document Type Commands =============


class CreateDocumentTypeCommand(BaseModel):
    """Create document type command"""

    tenant_id: UUID
    category_id: UUID
    name: str
    description: Optional[str] = None
    file_extensions: Optional[list[str]] = None
    max_file_size: int = 10485760
    retention_days: Optional[int] = None
    custom_attributes: Optional[list[dict[str, Any]]] = None


class CreateDocumentTypeHandler:
    """Handler for creating document types"""

    def __init__(self, db: Session):
        self.service = MasterDataService(db)

    async def handle(self, cmd: CreateDocumentTypeCommand) -> DocumentTypeResponse:
        """Create a new document type

        Args:
            cmd: Create command

        Returns:
            Created document type response
        """
        doc_type = await self.service.create_document_type(
            tenant_id=cmd.tenant_id,
            category_id=cmd.category_id,
            name=cmd.name,
            description=cmd.description,
            file_extensions=cmd.file_extensions,
            max_file_size=cmd.max_file_size,
            retention_days=cmd.retention_days,
            custom_attributes=cmd.custom_attributes,
        )

        return DocumentTypeResponse(
            id=doc_type.id,
            tenant_id=doc_type.tenant_id,
            name=doc_type.name,
            description=doc_type.description,
            category_id=doc_type.category_id,
            file_extensions=doc_type.file_extensions,
            max_file_size=doc_type.max_file_size,
            retention_days=doc_type.retention_days,
            custom_attributes=doc_type.custom_attributes,
            is_active=doc_type.is_active,
            deleted_at=doc_type.deleted_at.isoformat() if doc_type.deleted_at else None,
        )


class UpdateDocumentTypeCommand(BaseModel):
    """Update document type command"""

    tenant_id: UUID
    type_id: UUID
    name: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[UUID] = None
    file_extensions: Optional[list[str]] = None
    max_file_size: Optional[int] = None
    retention_days: Optional[int] = None
    custom_attributes: Optional[list[dict[str, Any]]] = None
    is_active: Optional[bool] = None


class UpdateDocumentTypeHandler:
    """Handler for updating document types"""

    def __init__(self, db: Session):
        self.service = MasterDataService(db)

    async def handle(self, cmd: UpdateDocumentTypeCommand) -> DocumentTypeResponse:
        """Update a document type

        Args:
            cmd: Update command

        Returns:
            Updated document type response
        """
        doc_type = await self.service.update_document_type(
            type_id=cmd.type_id,
            tenant_id=cmd.tenant_id,
            name=cmd.name,
            description=cmd.description,
            category_id=cmd.category_id,
            file_extensions=cmd.file_extensions,
            max_file_size=cmd.max_file_size,
            retention_days=cmd.retention_days,
            custom_attributes=cmd.custom_attributes,
            is_active=cmd.is_active,
        )

        return DocumentTypeResponse(
            id=doc_type.id,
            tenant_id=doc_type.tenant_id,
            name=doc_type.name,
            description=doc_type.description,
            category_id=doc_type.category_id,
            file_extensions=doc_type.file_extensions,
            max_file_size=doc_type.max_file_size,
            retention_days=doc_type.retention_days,
            custom_attributes=doc_type.custom_attributes,
            is_active=doc_type.is_active,
            deleted_at=doc_type.deleted_at.isoformat() if doc_type.deleted_at else None,
        )


class DeleteDocumentTypeCommand(BaseModel):
    """Delete document type command"""

    tenant_id: UUID
    type_id: UUID


class DeleteDocumentTypeHandler:
    """Handler for deleting document types"""

    def __init__(self, db: Session):
        self.service = MasterDataService(db)

    async def handle(self, cmd: DeleteDocumentTypeCommand) -> bool:
        """Delete a document type (soft delete)

        Args:
            cmd: Delete command

        Returns:
            True if deleted
        """
        return await self.service.delete_document_type(cmd.type_id, cmd.tenant_id)


class RestoreDocumentTypeCommand(BaseModel):
    """Restore document type command"""

    tenant_id: UUID
    type_id: UUID


class RestoreDocumentTypeHandler:
    """Handler for restoring deleted document types"""

    def __init__(self, db: Session):
        self.service = MasterDataService(db)

    async def handle(self, cmd: RestoreDocumentTypeCommand) -> bool:
        """Restore a soft-deleted document type

        Args:
            cmd: Restore command

        Returns:
            True if restored
        """
        return await self.service.restore_document_type(cmd.type_id, cmd.tenant_id)
