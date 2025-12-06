"""Folder repository with tree traversal and path operations."""

from typing import Optional
from uuid import UUID

from sqlmodel import Session, select

from tenant_service.exceptions import ResourceNotFoundError, ValidationError
from tenant_service.infrastructure.models.folder import Folder


class FolderRepository:
    """Repository for folder operations with tenant isolation."""

    def create(
        self,
        db: Session,
        user_tenant_id: UUID,
        owner_id: UUID,
        name: str,
        path: str,
        parent_id: Optional[UUID] = None,
        description: Optional[str] = None,
    ) -> Folder:
        """Create new folder."""
        # Calculate depth based on parent
        depth = 0
        if parent_id:
            parent = self.get_by_id(db, user_tenant_id, parent_id)
            depth = parent.depth + 1
            if depth > 20:
                raise ValidationError("Maximum folder nesting depth exceeded (20 levels)")

        folder = Folder(
            tenant_id=user_tenant_id,
            parent_id=parent_id,
            name=name,
            path=path,
            description=description,
            owner_id=owner_id,
            depth=depth,
        )
        db.add(folder)
        db.commit()
        db.refresh(folder)
        return folder

    def get_by_id(self, db: Session, user_tenant_id: UUID, folder_id: UUID) -> Folder:
        """Get folder by ID with tenant verification."""
        statement = select(Folder).where((Folder.id == folder_id) & (Folder.tenant_id == user_tenant_id))
        folder = db.exec(statement).first()
        if not folder:
            raise ResourceNotFoundError(f"Folder {folder_id} not found")
        return folder

    def get_by_path(self, db: Session, user_tenant_id: UUID, path: str) -> Optional[Folder]:
        """Get folder by path."""
        statement = select(Folder).where(
            (Folder.tenant_id == user_tenant_id) & (Folder.path == path) & (Folder.deleted_at.is_(None))
        )
        return db.exec(statement).first()

    def list_by_parent(
        self,
        db: Session,
        user_tenant_id: UUID,
        parent_id: Optional[UUID] = None,
        include_archived: bool = False,
    ) -> list[Folder]:
        """List children of folder."""
        statement = select(Folder).where((Folder.tenant_id == user_tenant_id) & (Folder.parent_id == parent_id))
        if not include_archived:
            statement = statement.where(Folder.is_archived.is_(False))

        statement = statement.order_by(Folder.name)
        return db.exec(statement).all()

    def list_by_tenant(
        self,
        db: Session,
        user_tenant_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Folder]:
        """List all folders for tenant (excludes soft-deleted)."""
        statement = (
            select(Folder)
            .where((Folder.tenant_id == user_tenant_id) & (Folder.deleted_at.is_(None)))
            .order_by(Folder.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return db.exec(statement).all()

    def get_root_folders(self, db: Session, user_tenant_id: UUID) -> list[Folder]:
        """Get top-level folders (parent_id is null)."""
        statement = select(Folder).where(
            (Folder.tenant_id == user_tenant_id) & (Folder.parent_id.is_(None)) & (Folder.deleted_at.is_(None))
        )
        return db.exec(statement).all()

    def list_all_descendants(self, db: Session, user_tenant_id: UUID, parent_id: UUID) -> list[Folder]:
        """Get all descendants of folder recursively."""
        # Get direct children
        children = self.list_by_parent(db, user_tenant_id, parent_id, include_archived=False)

        descendants = list(children)
        for child in children:
            descendants.extend(self.list_all_descendants(db, user_tenant_id, child.id))

        return descendants

    def update(
        self,
        db: Session,
        user_tenant_id: UUID,
        folder_id: UUID,
        **kwargs,
    ) -> Folder:
        """Update folder fields."""
        folder = self.get_by_id(db, user_tenant_id, folder_id)

        allowed_fields = {"name", "description", "is_archived", "path"}
        for field, value in kwargs.items():
            if field in allowed_fields and value is not None:
                setattr(folder, field, value)

        db.add(folder)
        db.commit()
        db.refresh(folder)
        return folder

    def soft_delete(self, db: Session, user_tenant_id: UUID, folder_id: UUID) -> None:
        """Soft delete folder."""
        from datetime import datetime

        folder = self.get_by_id(db, user_tenant_id, folder_id)
        folder.deleted_at = datetime.utcnow()
        db.add(folder)
        db.commit()

    def get_parent(self, db: Session, user_tenant_id: UUID, folder_id: UUID) -> Optional[Folder]:
        """Get parent folder."""
        folder = self.get_by_id(db, user_tenant_id, folder_id)
        if not folder.parent_id:
            return None
        return self.get_by_id(db, user_tenant_id, folder.parent_id)

    def increment_child_count(self, db: Session, user_tenant_id: UUID, folder_id: UUID) -> None:
        """Increment child count."""
        folder = self.get_by_id(db, user_tenant_id, folder_id)
        folder.child_count += 1
        db.add(folder)
        db.commit()

    def decrement_child_count(self, db: Session, user_tenant_id: UUID, folder_id: UUID) -> None:
        """Decrement child count."""
        folder = self.get_by_id(db, user_tenant_id, folder_id)
        if folder.child_count > 0:
            folder.child_count -= 1
        db.add(folder)
        db.commit()

    def path_exists(self, db: Session, user_tenant_id: UUID, path: str) -> bool:
        """Check if path exists for tenant."""
        statement = select(Folder).where(
            (Folder.tenant_id == user_tenant_id) & (Folder.path == path) & (Folder.deleted_at.is_(None))
        )
        return db.exec(statement).first() is not None
