"""CQRS handlers for folder deletion and restoration."""

import logging
from uuid import UUID

from sqlmodel import Session

from tenant_service.domain.services.folder_service import FolderService

logger = logging.getLogger(__name__)


class DeleteFolderCommand:
    """Command to delete folder (cascade)."""

    def __init__(self, user_tenant_id: UUID, user_id: UUID, folder_id: UUID):
        self.user_tenant_id = user_tenant_id
        self.user_id = user_id
        self.folder_id = folder_id


class RestoreFolderCommand:
    """Command to restore deleted folder."""

    def __init__(self, user_tenant_id: UUID, user_id: UUID, folder_id: UUID):
        self.user_tenant_id = user_tenant_id
        self.user_id = user_id
        self.folder_id = folder_id


class DeleteFolderHandler:
    """Handle folder deletion command (cascade to children)."""

    def __init__(self, service: FolderService):
        self.service = service

    def handle(self, db: Session, command: DeleteFolderCommand):
        """Execute delete folder command."""
        logger.info(
            f"Deleting folder {command.folder_id} (cascade to children)"
        )
        self.service.delete_folder(
            db=db,
            user_tenant_id=command.user_tenant_id,
            user_id=command.user_id,
            folder_id=command.folder_id,
        )
        logger.info(f"Folder {command.folder_id} and children deleted successfully")


class RestoreFolderHandler:
    """Handle folder restoration command."""

    def __init__(self, service: FolderService):
        self.service = service

    def handle(self, db: Session, command: RestoreFolderCommand):
        """Execute restore folder command."""
        logger.info(f"Restoring folder {command.folder_id}")
        self.service.restore_folder(
            db=db,
            user_tenant_id=command.user_tenant_id,
            user_id=command.user_id,
            folder_id=command.folder_id,
        )
        logger.info(f"Folder {command.folder_id} restored successfully")
