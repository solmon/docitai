"""Query handlers for folder operations."""

import logging
from uuid import UUID

from sqlmodel import Session

from tenant_service.domain.services.folder_service import FolderService

logger = logging.getLogger(__name__)


class GetFolderTreeQuery:
    """Query to get folder with tree structure."""

    def __init__(self, user_tenant_id: UUID, folder_id: UUID):
        self.user_tenant_id = user_tenant_id
        self.folder_id = folder_id


class GetBreadcrumbQuery:
    """Query to get breadcrumb navigation."""

    def __init__(self, user_tenant_id: UUID, folder_id: UUID):
        self.user_tenant_id = user_tenant_id
        self.folder_id = folder_id


class GetFolderTreeHandler:
    """Handle get folder tree query."""

    def __init__(self, service: FolderService):
        self.service = service

    def handle(self, db: Session, query: GetFolderTreeQuery):
        """Execute get folder tree query."""
        logger.info(f"Fetching folder tree for {query.folder_id}")
        tree = self.service.get_folder_tree(
            db=db,
            user_tenant_id=query.user_tenant_id,
            folder_id=query.folder_id,
        )
        logger.info(f"Folder tree fetched successfully")
        return tree


class GetBreadcrumbHandler:
    """Handle get breadcrumb query."""

    def __init__(self, service: FolderService):
        self.service = service

    def handle(self, db: Session, query: GetBreadcrumbQuery):
        """Execute get breadcrumb query."""
        logger.info(f"Fetching breadcrumb for folder {query.folder_id}")
        breadcrumb = self.service.get_breadcrumb(
            db=db,
            user_tenant_id=query.user_tenant_id,
            folder_id=query.folder_id,
        )
        logger.info(f"Breadcrumb fetched successfully")
        return breadcrumb
