"""CQRS handlers for folder operations."""

import logging
from uuid import UUID

from sqlmodel import Session

from tenant_service.domain.services.folder_service import FolderService
from tenant_service.infrastructure.models.folder import FolderCreate, FolderUpdate, FolderMove

logger = logging.getLogger(__name__)


class CreateFolderCommand:
    """Command to create folder."""

    def __init__(self, user_tenant_id: UUID, user_id: UUID, data: FolderCreate):
        self.user_tenant_id = user_tenant_id
        self.user_id = user_id
        self.data = data


class UpdateFolderCommand:
    """Command to update folder."""

    def __init__(self, user_tenant_id: UUID, user_id: UUID, folder_id: UUID, data: FolderUpdate):
        self.user_tenant_id = user_tenant_id
        self.user_id = user_id
        self.folder_id = folder_id
        self.data = data


class MoveFolderCommand:
    """Command to move folder."""

    def __init__(self, user_tenant_id: UUID, user_id: UUID, folder_id: UUID, data: FolderMove):
        self.user_tenant_id = user_tenant_id
        self.user_id = user_id
        self.folder_id = folder_id
        self.data = data


class CreateFolderHandler:
    """Handle folder creation command."""

    def __init__(self, service: FolderService):
        self.service = service

    def handle(self, db: Session, command: CreateFolderCommand):
        """Execute create folder command."""
        logger.info(f"Creating folder '{command.data.name}' for tenant {command.user_tenant_id}")
        folder = self.service.create_folder(
            db=db,
            user_tenant_id=command.user_tenant_id,
            user_id=command.user_id,
            data=command.data,
        )
        logger.info(f"Folder {folder.id} created at path {folder.path}")
        return folder


class UpdateFolderHandler:
    """Handle folder update command."""

    def __init__(self, service: FolderService):
        self.service = service

    def handle(self, db: Session, command: UpdateFolderCommand):
        """Execute update folder command."""
        logger.info(f"Updating folder {command.folder_id}")
        folder = self.service.update_folder(
            db=db,
            user_tenant_id=command.user_tenant_id,
            user_id=command.user_id,
            folder_id=command.folder_id,
            data=command.data,
        )
        logger.info(f"Folder {command.folder_id} updated successfully")
        return folder


class MoveFolderHandler:
    """Handle folder move command."""

    def __init__(self, service: FolderService):
        self.service = service

    def handle(self, db: Session, command: MoveFolderCommand):
        """Execute move folder command."""
        logger.info(f"Moving folder {command.folder_id} to parent {command.data.new_parent_id}")
        folder = self.service.move_folder(
            db=db,
            user_tenant_id=command.user_tenant_id,
            user_id=command.user_id,
            folder_id=command.folder_id,
            new_parent_id=command.data.new_parent_id,
        )
        logger.info(f"Folder {command.folder_id} moved to path {folder.path}")
        return folder
