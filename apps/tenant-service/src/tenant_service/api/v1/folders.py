"""REST API endpoints for folder management."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

from tenant_service.api.dependencies import get_current_user, get_db
from tenant_service.application.handlers.folder_deletion_handler import (
    DeleteFolderCommand,
    DeleteFolderHandler,
    RestoreFolderCommand,
    RestoreFolderHandler,
)
from tenant_service.application.handlers.folder_handler import (
    CreateFolderCommand,
    CreateFolderHandler,
    MoveFolderCommand,
    MoveFolderHandler,
    UpdateFolderCommand,
    UpdateFolderHandler,
)
from tenant_service.application.handlers.folder_query_handler import (
    GetBreadcrumbHandler,
    GetBreadcrumbQuery,
    GetFolderTreeHandler,
    GetFolderTreeQuery,
)
from tenant_service.domain.services.folder_service import FolderService
from tenant_service.exceptions import ResourceNotFoundError, TenantServiceException
from tenant_service.infrastructure.models.folder import (
    BreadcrumbResponse,
    BreadcrumbItem,
    FolderCreate,
    FolderMove,
    FolderResponse,
    FolderTreeResponse,
    FolderUpdate,
)
from tenant_service.infrastructure.repositories.compliance_audit_repository import (
    ComplianceAuditRepository,
)
from tenant_service.infrastructure.repositories.folder_repository import FolderRepository

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/folders", tags=["Folders"])


@router.post("", response_model=FolderResponse, status_code=status.HTTP_201_CREATED)
async def create_folder(
    data: FolderCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Create new folder."""
    try:
        folder_repo = FolderRepository()
        audit_repo = ComplianceAuditRepository()
        service = FolderService(folder_repo, audit_repo)
        handler = CreateFolderHandler(service)

        command = CreateFolderCommand(
            user_tenant_id=user.tenant_id,
            user_id=user.id,
            data=data,
        )
        folder = handler.handle(db, command)
        return folder
    except TenantServiceException as e:
        logger.error(f"Failed to create folder: {e}")
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error creating folder: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/{folder_id}", response_model=FolderResponse)
async def get_folder(
    folder_id: UUID,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Get folder by ID."""
    try:
        folder_repo = FolderRepository()
        audit_repo = ComplianceAuditRepository()
        service = FolderService(folder_repo, audit_repo)
        folder = service.get_folder(db, user.tenant_id, folder_id)
        return folder
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error fetching folder: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("", response_model=list[FolderResponse])
async def list_root_folders(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """List root folders for tenant."""
    try:
        folder_repo = FolderRepository()
        audit_repo = ComplianceAuditRepository()
        service = FolderService(folder_repo, audit_repo)
        folders = service.list_root_folders(db, user.tenant_id)
        return folders[offset : offset + limit]
    except Exception as e:
        logger.error(f"Error listing folders: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/{folder_id}/children", response_model=list[FolderResponse])
async def get_folder_children(
    folder_id: UUID,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Get children of folder."""
    try:
        folder_repo = FolderRepository()
        audit_repo = ComplianceAuditRepository()
        service = FolderService(folder_repo, audit_repo)

        # Verify folder exists
        service.get_folder(db, user.tenant_id, folder_id)

        children = folder_repo.list_by_parent(db, user.tenant_id, folder_id)
        return children[offset : offset + limit]
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error fetching children: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/{folder_id}/tree", response_model=FolderTreeResponse)
async def get_folder_tree(
    folder_id: UUID,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Get folder with recursive tree structure."""
    try:
        folder_repo = FolderRepository()
        audit_repo = ComplianceAuditRepository()
        service = FolderService(folder_repo, audit_repo)
        handler = GetFolderTreeHandler(service)

        query = GetFolderTreeQuery(user_tenant_id=user.tenant_id, folder_id=folder_id)
        tree = handler.handle(db, query)
        return tree
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error fetching folder tree: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.put("/{folder_id}", response_model=FolderResponse)
async def update_folder(
    folder_id: UUID,
    data: FolderUpdate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Update folder."""
    try:
        folder_repo = FolderRepository()
        audit_repo = ComplianceAuditRepository()
        service = FolderService(folder_repo, audit_repo)
        handler = UpdateFolderHandler(service)

        command = UpdateFolderCommand(
            user_tenant_id=user.tenant_id,
            user_id=user.id,
            folder_id=folder_id,
            data=data,
        )
        folder = handler.handle(db, command)
        return folder
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except TenantServiceException as e:
        logger.error(f"Failed to update folder: {e}")
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error updating folder: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post("/{folder_id}/move", response_model=FolderResponse)
async def move_folder(
    folder_id: UUID,
    data: FolderMove,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Move folder to new parent."""
    try:
        folder_repo = FolderRepository()
        audit_repo = ComplianceAuditRepository()
        service = FolderService(folder_repo, audit_repo)
        handler = MoveFolderHandler(service)

        command = MoveFolderCommand(
            user_tenant_id=user.tenant_id,
            user_id=user.id,
            folder_id=folder_id,
            data=data,
        )
        folder = handler.handle(db, command)
        return folder
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except TenantServiceException as e:
        logger.error(f"Failed to move folder: {e}")
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error moving folder: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.delete("/{folder_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_folder(
    folder_id: UUID,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Delete folder (cascade to children)."""
    try:
        folder_repo = FolderRepository()
        audit_repo = ComplianceAuditRepository()
        service = FolderService(folder_repo, audit_repo)
        handler = DeleteFolderHandler(service)

        command = DeleteFolderCommand(
            user_tenant_id=user.tenant_id,
            user_id=user.id,
            folder_id=folder_id,
        )
        handler.handle(db, command)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting folder: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post("/{folder_id}/restore", status_code=status.HTTP_204_NO_CONTENT)
async def restore_folder(
    folder_id: UUID,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Restore deleted folder."""
    try:
        folder_repo = FolderRepository()
        audit_repo = ComplianceAuditRepository()
        service = FolderService(folder_repo, audit_repo)
        handler = RestoreFolderHandler(service)

        command = RestoreFolderCommand(
            user_tenant_id=user.tenant_id,
            user_id=user.id,
            folder_id=folder_id,
        )
        handler.handle(db, command)
    except Exception as e:
        logger.error(f"Error restoring folder: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/{folder_id}/breadcrumb", response_model=BreadcrumbResponse)
async def get_breadcrumb(
    folder_id: UUID,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Get breadcrumb navigation for folder."""
    try:
        folder_repo = FolderRepository()
        audit_repo = ComplianceAuditRepository()
        service = FolderService(folder_repo, audit_repo)
        handler = GetBreadcrumbHandler(service)

        query = GetBreadcrumbQuery(user_tenant_id=user.tenant_id, folder_id=folder_id)
        breadcrumb_items = handler.handle(db, query)

        # Convert to response format
        current = breadcrumb_items[-1]
        parents = breadcrumb_items[:-1]

        return BreadcrumbResponse(
            current=BreadcrumbItem(**current),
            parents=[BreadcrumbItem(**item) for item in parents],
            full_path=current["path"],
        )
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error fetching breadcrumb: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")
