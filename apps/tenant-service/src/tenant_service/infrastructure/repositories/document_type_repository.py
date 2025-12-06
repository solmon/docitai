"""Document Type Repository - Data Access Layer

Implements CRUD operations for document types with tenant isolation.
"""

from typing import Optional
from uuid import UUID

from sqlalchemy import and_, select
from sqlmodel import Session

from tenant_service.infrastructure.models.document_type import DocumentType


class DocumentTypeRepository:
    """Repository for Document Type data access"""

    def __init__(self, db: Session):
        self.db = db

    async def create(self, doc_type: DocumentType) -> DocumentType:
        """Create a new document type

        Args:
            doc_type: DocumentType entity to create

        Returns:
            Created type with ID
        """
        self.db.add(doc_type)
        await self.db.commit()
        await self.db.refresh(doc_type)
        return doc_type

    async def get_by_id(self, type_id: UUID, tenant_id: UUID) -> Optional[DocumentType]:
        """Get document type by ID with tenant verification

        Args:
            type_id: Document type ID
            tenant_id: Tenant ID for isolation

        Returns:
            Document type if found, None otherwise
        """
        stmt = select(DocumentType).where(
            and_(
                DocumentType.id == type_id,
                DocumentType.tenant_id == tenant_id,
                DocumentType.deleted_at.is_(None),
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_tenant(self, tenant_id: UUID, skip: int = 0, limit: int = 50) -> list[DocumentType]:
        """List all document types for a tenant

        Args:
            tenant_id: Tenant ID
            skip: Pagination offset
            limit: Pagination limit

        Returns:
            List of document types (paginated)
        """
        stmt = (
            select(DocumentType)
            .where(
                and_(
                    DocumentType.tenant_id == tenant_id,
                    DocumentType.deleted_at.is_(None),
                )
            )
            .order_by(DocumentType.name)
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def list_by_category(self, category_id: UUID, tenant_id: UUID) -> list[DocumentType]:
        """Get document types by category

        Args:
            category_id: Category ID
            tenant_id: Tenant ID

        Returns:
            List of document types in category
        """
        stmt = select(DocumentType).where(
            and_(
                DocumentType.tenant_id == tenant_id,
                DocumentType.category_id == category_id,
                DocumentType.deleted_at.is_(None),
            )
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def list_active(self, tenant_id: UUID) -> list[DocumentType]:
        """Get only active document types

        Args:
            tenant_id: Tenant ID

        Returns:
            List of active document types
        """
        stmt = select(DocumentType).where(
            and_(
                DocumentType.tenant_id == tenant_id,
                DocumentType.is_active.is_(True),
                DocumentType.deleted_at.is_(None),
            )
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def update(self, doc_type: DocumentType) -> DocumentType:
        """Update an existing document type

        Args:
            doc_type: DocumentType with updated fields

        Returns:
            Updated document type
        """
        self.db.add(doc_type)
        await self.db.commit()
        await self.db.refresh(doc_type)
        return doc_type

    async def soft_delete(self, type_id: UUID, tenant_id: UUID) -> bool:
        """Soft delete a document type

        Args:
            type_id: Document type ID
            tenant_id: Tenant ID

        Returns:
            True if deleted, False if not found
        """
        doc_type = await self.get_by_id(type_id, tenant_id)
        if not doc_type:
            return False

        from datetime import datetime, timezone

        doc_type.deleted_at = datetime.now(timezone.utc)
        await self.update(doc_type)
        return True

    async def restore(self, type_id: UUID, tenant_id: UUID) -> bool:
        """Restore a soft-deleted document type

        Args:
            type_id: Document type ID
            tenant_id: Tenant ID

        Returns:
            True if restored, False if not found
        """
        stmt = select(DocumentType).where(
            and_(
                DocumentType.id == type_id,
                DocumentType.tenant_id == tenant_id,
                DocumentType.deleted_at.isnot(None),
            )
        )
        result = await self.db.execute(stmt)
        doc_type = result.scalar_one_or_none()

        if not doc_type:
            return False

        doc_type.deleted_at = None
        await self.update(doc_type)
        return True

    async def exists_by_name(self, name: str, tenant_id: UUID) -> bool:
        """Check if document type with name exists

        Args:
            name: Document type name
            tenant_id: Tenant ID

        Returns:
            True if exists, False otherwise
        """
        stmt = select(DocumentType).where(
            and_(
                DocumentType.name == name,
                DocumentType.tenant_id == tenant_id,
                DocumentType.deleted_at.is_(None),
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def count_by_category(self, category_id: UUID, tenant_id: UUID) -> int:
        """Count document types in category

        Args:
            category_id: Category ID
            tenant_id: Tenant ID

        Returns:
            Number of active types in category
        """
        stmt = select(DocumentType).where(
            and_(
                DocumentType.tenant_id == tenant_id,
                DocumentType.category_id == category_id,
                DocumentType.deleted_at.is_(None),
            )
        )
        result = await self.db.execute(stmt)
        return len(result.scalars().all())

    async def count_by_tenant(self, tenant_id: UUID) -> int:
        """Count all document types for tenant

        Args:
            tenant_id: Tenant ID

        Returns:
            Number of active types
        """
        stmt = select(DocumentType).where(
            and_(
                DocumentType.tenant_id == tenant_id,
                DocumentType.deleted_at.is_(None),
            )
        )
        result = await self.db.execute(stmt)
        return len(result.scalars().all())

    async def get_by_file_extension(self, extension: str, tenant_id: UUID) -> list[DocumentType]:
        """Find document types that support a file extension

        Args:
            extension: File extension (e.g., '.pdf')
            tenant_id: Tenant ID

        Returns:
            List of document types supporting the extension
        """
        # This requires in-memory filtering since file_extensions is JSON
        stmt = select(DocumentType).where(
            and_(
                DocumentType.tenant_id == tenant_id,
                DocumentType.deleted_at.is_(None),
            )
        )
        result = await self.db.execute(stmt)
        all_types = result.scalars().all()

        # Filter by extension
        return [dt for dt in all_types if extension.lower() in [ext.lower() for ext in dt.file_extensions]]
