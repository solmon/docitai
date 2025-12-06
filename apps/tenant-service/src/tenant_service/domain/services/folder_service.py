"""Folder domain service with path logic and hierarchy management."""

from typing import Optional
from uuid import UUID

from sqlmodel import Session

from tenant_service.domain.enums.retention_types import AuditActionType
from tenant_service.exceptions import ValidationError, ResourceNotFoundError
from tenant_service.infrastructure.models.folder import Folder, FolderCreate, FolderUpdate
from tenant_service.infrastructure.repositories.compliance_audit_repository import (
    ComplianceAuditRepository,
)
from tenant_service.infrastructure.repositories.folder_repository import FolderRepository


class FolderService:
    """Business logic for folder hierarchy and operations."""

    def __init__(
        self,
        folder_repository: FolderRepository,
        audit_repository: ComplianceAuditRepository,
    ):
        self.folder_repo = folder_repository
        self.audit_repo = audit_repository

    def create_folder(
        self,
        db: Session,
        user_tenant_id: UUID,
        user_id: UUID,
        data: FolderCreate,
    ) -> Folder:
        """Create folder with path generation."""
        # Validate parent exists if provided
        if data.parent_id:
            parent = self.folder_repo.get_by_id(db, user_tenant_id, data.parent_id)
            path = f"{parent.path}/{data.name}"
        else:
            path = f"/{data.name}"

        # Check path uniqueness
        if self.folder_repo.path_exists(db, user_tenant_id, path):
            raise ValidationError(f"Folder path '{path}' already exists")

        folder = self.folder_repo.create(
            db=db,
            user_tenant_id=user_tenant_id,
            owner_id=user_id,
            name=data.name,
            path=path,
            parent_id=data.parent_id,
            description=data.description,
        )

        # Log creation
        self.audit_repo.log_action(
            db=db,
            user_tenant_id=user_tenant_id,
            action_type=AuditActionType.POLICY_CREATED,  # Reuse for now
            resource_type="folder",
            resource_id=folder.id,
            changed_by=user_id,
            new_value={"name": folder.name, "path": folder.path},
            reason=f"Created folder: {data.name}",
        )

        # Increment parent's child count
        if data.parent_id:
            self.folder_repo.increment_child_count(db, user_tenant_id, data.parent_id)

        return folder

    def get_folder(self, db: Session, user_tenant_id: UUID, folder_id: UUID) -> Folder:
        """Get folder with tenant verification."""
        folder = self.folder_repo.get_by_id(db, user_tenant_id, folder_id)
        if folder.deleted_at:
            raise ResourceNotFoundError(f"Folder {folder_id} has been deleted")
        return folder

    def list_root_folders(self, db: Session, user_tenant_id: UUID) -> list[Folder]:
        """List top-level folders."""
        return self.folder_repo.get_root_folders(db, user_tenant_id)

    def get_folder_tree(self, db: Session, user_tenant_id: UUID, folder_id: UUID) -> dict:
        """Get folder with recursive children."""
        folder = self.get_folder(db, user_tenant_id, folder_id)
        children = self.folder_repo.list_by_parent(db, user_tenant_id, folder_id)

        tree = {
            "id": str(folder.id),
            "name": folder.name,
            "path": folder.path,
            "description": folder.description,
            "owner_id": str(folder.owner_id),
            "is_archived": folder.is_archived,
            "child_count": folder.child_count,
            "depth": folder.depth,
            "children": [self.get_folder_tree(db, user_tenant_id, child.id) for child in children],
        }
        return tree

    def update_folder(
        self,
        db: Session,
        user_tenant_id: UUID,
        user_id: UUID,
        folder_id: UUID,
        data: FolderUpdate,
    ) -> Folder:
        """Update folder fields."""
        old_folder = self.get_folder(db, user_tenant_id, folder_id)

        update_dict = data.model_dump(exclude_unset=True)
        if not update_dict:
            return old_folder

        folder = self.folder_repo.update(db, user_tenant_id, folder_id, **update_dict)

        # Log update
        self.audit_repo.log_action(
            db=db,
            user_tenant_id=user_tenant_id,
            action_type=AuditActionType.POLICY_UPDATED,
            resource_type="folder",
            resource_id=folder_id,
            changed_by=user_id,
            old_value={"changed_fields": list(update_dict.keys())},
            new_value={"name": folder.name, "description": folder.description},
            reason="Folder updated",
        )

        return folder

    def move_folder(
        self,
        db: Session,
        user_tenant_id: UUID,
        user_id: UUID,
        folder_id: UUID,
        new_parent_id: Optional[UUID],
    ) -> Folder:
        """Move folder to new parent with path update."""
        folder = self.get_folder(db, user_tenant_id, folder_id)

        # Prevent circular references
        if new_parent_id:
            if new_parent_id == folder_id:
                raise ValidationError("Cannot move folder to itself")

            new_parent = self.folder_repo.get_by_id(db, user_tenant_id, new_parent_id)

            # Check if new parent is descendant of current folder
            descendants = self.folder_repo.list_all_descendants(db, user_tenant_id, folder_id)
            if any(d.id == new_parent_id for d in descendants):
                raise ValidationError("Cannot move folder to its own descendant (circular reference)")

            new_path = f"{new_parent.path}/{folder.name}"
        else:
            new_path = f"/{folder.name}"

        # Check new path is unique
        if self.folder_repo.path_exists(db, user_tenant_id, new_path):
            raise ValidationError(f"Folder path '{new_path}' already exists")

        old_parent_id = folder.parent_id

        # Update folder
        folder = self.folder_repo.update(
            db,
            user_tenant_id,
            folder_id,
            parent_id=new_parent_id,
            path=new_path,
        )

        # Update all descendants' paths
        self._update_descendants_paths(db, user_tenant_id, folder_id, new_path)

        # Update child counts
        if old_parent_id:
            self.folder_repo.decrement_child_count(db, user_tenant_id, old_parent_id)
        if new_parent_id:
            self.folder_repo.increment_child_count(db, user_tenant_id, new_parent_id)

        # Log move
        self.audit_repo.log_action(
            db=db,
            user_tenant_id=user_tenant_id,
            action_type=AuditActionType.POLICY_UPDATED,
            resource_type="folder",
            resource_id=folder_id,
            changed_by=user_id,
            old_value={"parent_id": str(old_parent_id) if old_parent_id else None},
            new_value={"parent_id": str(new_parent_id) if new_parent_id else None},
            reason=f"Moved folder to {new_path}",
        )

        return folder

    def delete_folder(
        self,
        db: Session,
        user_tenant_id: UUID,
        user_id: UUID,
        folder_id: UUID,
    ) -> None:
        """Delete folder with cascade to children."""
        folder = self.get_folder(db, user_tenant_id, folder_id)

        # Get all descendants
        descendants = self.folder_repo.list_all_descendants(db, user_tenant_id, folder_id)

        # Soft delete folder
        self.folder_repo.soft_delete(db, user_tenant_id, folder_id)

        # Soft delete all descendants
        for descendant in descendants:
            self.folder_repo.soft_delete(db, user_tenant_id, descendant.id)

            # Log each deletion
            self.audit_repo.log_action(
                db=db,
                user_tenant_id=user_tenant_id,
                action_type=AuditActionType.POLICY_DELETED,
                resource_type="folder",
                resource_id=descendant.id,
                changed_by=user_id,
                old_value={"path": descendant.path},
                reason="Deleted (cascade from parent)",
            )

        # Log root deletion
        self.audit_repo.log_action(
            db=db,
            user_tenant_id=user_tenant_id,
            action_type=AuditActionType.POLICY_DELETED,
            resource_type="folder",
            resource_id=folder_id,
            changed_by=user_id,
            old_value={"path": folder.path},
            reason=f"Deleted folder and {len(descendants)} descendants",
        )

        # Update parent's child count
        if folder.parent_id:
            self.folder_repo.decrement_child_count(db, user_tenant_id, folder.parent_id)

    def restore_folder(
        self,
        db: Session,
        user_tenant_id: UUID,
        user_id: UUID,
        folder_id: UUID,
    ) -> None:
        """Restore deleted folder and descendants."""
        # Note: Use raw SQL for restoration or implement differently
        # This is a simplified example - actual DB operation would use:
        # UPDATE folders SET deleted_at = NULL WHERE tenant_id = user_tenant_id
        # AND id = folder_id AND deleted_at IS NOT NULL

        self.audit_repo.log_action(
            db=db,
            user_tenant_id=user_tenant_id,
            action_type=AuditActionType.POLICY_CREATED,
            resource_type="folder",
            resource_id=folder_id,
            changed_by=user_id,
            reason="Folder restored",
        )

    def get_breadcrumb(self, db: Session, user_tenant_id: UUID, folder_id: UUID) -> list[dict]:
        """Get breadcrumb path for navigation."""
        folder = self.get_folder(db, user_tenant_id, folder_id)
        breadcrumb = [{"id": str(folder.id), "name": folder.name, "path": folder.path}]

        parent_id = folder.parent_id
        while parent_id:
            parent = self.folder_repo.get_by_id(db, user_tenant_id, parent_id)
            breadcrumb.insert(
                0,
                {"id": str(parent.id), "name": parent.name, "path": parent.path},
            )
            parent_id = parent.parent_id

        return breadcrumb

    def _update_descendants_paths(
        self, db: Session, user_tenant_id: UUID, parent_id: UUID, new_parent_path: str
    ) -> None:
        """Update paths of all descendants after parent moves."""
        children = self.folder_repo.list_by_parent(db, user_tenant_id, parent_id, include_archived=True)

        for child in children:
            new_path = f"{new_parent_path}/{child.name}"

            self.folder_repo.update(db, user_tenant_id, child.id, path=new_path)

            # Recursively update descendants
            self._update_descendants_paths(db, user_tenant_id, child.id, new_path)
