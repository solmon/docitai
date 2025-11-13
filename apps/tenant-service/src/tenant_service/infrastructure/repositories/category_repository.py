"""Document Category Repository - Data Access Layer

Implements CRUD operations for document categories with tenant isolation.
"""

from typing import Optional
from uuid import UUID

from sqlalchemy import and_, select
from sqlmodel import Session

from tenant_service.infrastructure.models.document_category import DocumentCategory


class DocumentCategoryRepository:
    """Repository for Document Category data access"""

    def __init__(self, db: Session):
        self.db = db

    async def create(self, category: DocumentCategory) -> DocumentCategory:
        """Create a new category
        
        Args:
            category: DocumentCategory entity to create
            
        Returns:
            Created category with ID
        """
        self.db.add(category)
        await self.db.commit()
        await self.db.refresh(category)
        return category

    async def get_by_id(
        self, category_id: UUID, tenant_id: UUID
    ) -> Optional[DocumentCategory]:
        """Get category by ID with tenant verification
        
        Args:
            category_id: Category ID
            tenant_id: Tenant ID for isolation
            
        Returns:
            Category if found, None otherwise
        """
        stmt = select(DocumentCategory).where(
            and_(
                DocumentCategory.id == category_id,
                DocumentCategory.tenant_id == tenant_id,
                DocumentCategory.deleted_at.is_(None),
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_tenant(
        self, tenant_id: UUID, skip: int = 0, limit: int = 50
    ) -> list[DocumentCategory]:
        """List all categories for a tenant
        
        Args:
            tenant_id: Tenant ID
            skip: Pagination offset
            limit: Pagination limit
            
        Returns:
            List of categories (paginated)
        """
        stmt = (
            select(DocumentCategory)
            .where(
                and_(
                    DocumentCategory.tenant_id == tenant_id,
                    DocumentCategory.deleted_at.is_(None),
                )
            )
            .order_by(DocumentCategory.sort_order, DocumentCategory.name)
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def list_root_categories(self, tenant_id: UUID) -> list[DocumentCategory]:
        """Get root categories (no parent)
        
        Args:
            tenant_id: Tenant ID
            
        Returns:
            List of root categories
        """
        stmt = select(DocumentCategory).where(
            and_(
                DocumentCategory.tenant_id == tenant_id,
                DocumentCategory.parent_category_id.is_(None),
                DocumentCategory.deleted_at.is_(None),
            )
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def list_by_parent(
        self, parent_id: UUID, tenant_id: UUID
    ) -> list[DocumentCategory]:
        """Get child categories by parent ID
        
        Args:
            parent_id: Parent category ID
            tenant_id: Tenant ID
            
        Returns:
            List of child categories
        """
        stmt = select(DocumentCategory).where(
            and_(
                DocumentCategory.tenant_id == tenant_id,
                DocumentCategory.parent_category_id == parent_id,
                DocumentCategory.deleted_at.is_(None),
            )
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_category_tree(
        self, tenant_id: UUID, parent_id: Optional[UUID] = None
    ) -> list[DocumentCategory]:
        """Get all categories in tree hierarchy
        
        Args:
            tenant_id: Tenant ID
            parent_id: Optional parent to limit subtree
            
        Returns:
            List of categories (no ordering - caller builds tree)
        """
        if parent_id:
            stmt = select(DocumentCategory).where(
                and_(
                    DocumentCategory.tenant_id == tenant_id,
                    DocumentCategory.deleted_at.is_(None),
                )
            )
        else:
            stmt = select(DocumentCategory).where(
                and_(
                    DocumentCategory.tenant_id == tenant_id,
                    DocumentCategory.deleted_at.is_(None),
                )
            )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def update(self, category: DocumentCategory) -> DocumentCategory:
        """Update an existing category
        
        Args:
            category: Category with updated fields
            
        Returns:
            Updated category
        """
        self.db.add(category)
        await self.db.commit()
        await self.db.refresh(category)
        return category

    async def soft_delete(self, category_id: UUID, tenant_id: UUID) -> bool:
        """Soft delete a category
        
        Args:
            category_id: Category ID
            tenant_id: Tenant ID
            
        Returns:
            True if deleted, False if not found
        """
        category = await self.get_by_id(category_id, tenant_id)
        if not category:
            return False

        from datetime import datetime, timezone
        category.deleted_at = datetime.now(timezone.utc)
        await self.update(category)
        return True

    async def restore(self, category_id: UUID, tenant_id: UUID) -> bool:
        """Restore a soft-deleted category
        
        Args:
            category_id: Category ID
            tenant_id: Tenant ID
            
        Returns:
            True if restored, False if not found
        """
        stmt = select(DocumentCategory).where(
            and_(
                DocumentCategory.id == category_id,
                DocumentCategory.tenant_id == tenant_id,
                DocumentCategory.deleted_at.isnot(None),
            )
        )
        result = await self.db.execute(stmt)
        category = result.scalar_one_or_none()

        if not category:
            return False

        category.deleted_at = None
        await self.update(category)
        return True

    async def exists_by_name(self, name: str, tenant_id: UUID) -> bool:
        """Check if category with name exists
        
        Args:
            name: Category name
            tenant_id: Tenant ID
            
        Returns:
            True if exists, False otherwise
        """
        stmt = select(DocumentCategory).where(
            and_(
                DocumentCategory.name == name,
                DocumentCategory.tenant_id == tenant_id,
                DocumentCategory.deleted_at.is_(None),
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def count_by_tenant(self, tenant_id: UUID) -> int:
        """Count active categories for tenant
        
        Args:
            tenant_id: Tenant ID
            
        Returns:
            Number of active categories
        """
        stmt = select(DocumentCategory).where(
            and_(
                DocumentCategory.tenant_id == tenant_id,
                DocumentCategory.deleted_at.is_(None),
            )
        )
        result = await self.db.execute(stmt)
        return len(result.scalars().all())

    async def get_descendants(
        self, parent_id: UUID, tenant_id: UUID
    ) -> list[DocumentCategory]:
        """Get all descendants of a category (recursive)
        
        Args:
            parent_id: Parent category ID
            tenant_id: Tenant ID
            
        Returns:
            List of all descendant categories
        """
        # Fetch all categories to do recursive search in-memory
        all_categories = await self.get_category_tree(tenant_id)

        descendants = []
        to_process = [parent_id]

        while to_process:
            current_id = to_process.pop(0)
            # Find children of current
            children = [
                c for c in all_categories
                if c.parent_category_id == current_id
                and c.deleted_at is None
            ]
            descendants.extend(children)
            to_process.extend([c.id for c in children])

        return descendants
