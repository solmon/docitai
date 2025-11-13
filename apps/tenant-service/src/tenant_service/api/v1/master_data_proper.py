"""Master Data REST API Endpoints

Provides REST endpoints for document categories and types management.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from sqlmodel import Session

from tenant_service.api.dependencies import UserDep, SessionDep
from tenant_service.application.handlers.master_data_handler import (
    CreateCategoryCommand,
    CreateCategoryHandler,
    CreateDocumentTypeCommand,
    CreateDocumentTypeHandler,
    DeleteCategoryCommand,
    DeleteCategoryHandler,
    DeleteDocumentTypeCommand,
    DeleteDocumentTypeHandler,
    RestoreCategoryCommand,
    RestoreCategoryHandler,
    RestoreDocumentTypeCommand,
    RestoreDocumentTypeHandler,
    UpdateCategoryCommand,
    UpdateCategoryHandler,
    UpdateDocumentTypeCommand,
    UpdateDocumentTypeHandler,
)
from tenant_service.domain.services.master_data_service import MasterDataService
from tenant_service.infrastructure.models.document_category import (
    DocumentCategoryCreate,
    DocumentCategoryResponse,
    DocumentCategoryTreeResponse,
    DocumentCategoryUpdate,
)
from tenant_service.infrastructure.models.document_type import (
    AttributeSchemaResponse,
    DocumentTypeCreate,
    DocumentTypeResponse,
    DocumentTypeUpdate,
)
from tenant_service.infrastructure.models.master_data_version import (
    MasterDataVersionResponse,
    MasterDataVersionHistory,
)
from tenant_service.infrastructure.repositories.category_repository import (
    DocumentCategoryRepository,
)
from tenant_service.infrastructure.repositories.document_type_repository import (
    DocumentTypeRepository,
)
from tenant_service.infrastructure.repositories.master_data_version_repository import (
    MasterDataVersionRepository,
)

router = APIRouter(prefix="/api/v1/master-data", tags=["master-data"])


@router.post("/categories", response_model=DocumentCategoryResponse)
async def create_category(
    request: DocumentCategoryCreate,
    user: UserDep,
    db: SessionDep,
) -> DocumentCategoryResponse:
    """Create a new document category"""
    try:
        handler = CreateCategoryHandler(db)
        cmd = CreateCategoryCommand(
            tenant_id=user.tenant_id,
            name=request.name,
            description=request.description,
            color_code=request.color_code,
            icon=request.icon,
            parent_category_id=request.parent_category_id,
            sort_order=request.sort_order,
        )
        return await handler.handle(cmd)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/categories", response_model=list[DocumentCategoryResponse])
async def list_categories(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    user: UserDep = None,
    db: SessionDep = None,
) -> list[DocumentCategoryResponse]:
    """List all categories for tenant"""
    repo = DocumentCategoryRepository(db)
    categories = await repo.list_by_tenant(user.tenant_id, skip, limit)
    return [
        DocumentCategoryResponse(
            id=c.id,
            tenant_id=c.tenant_id,
            name=c.name,
            description=c.description,
            color_code=c.color_code,
            icon=c.icon,
            parent_category_id=c.parent_category_id,
            sort_order=c.sort_order,
            is_active=c.is_active,
            deleted_at=c.deleted_at.isoformat() if c.deleted_at else None,
        )
        for c in categories
    ]


@router.get("/categories/{id}", response_model=DocumentCategoryResponse)
async def get_category(
    id: UUID,
    user: UserDep,
    db: SessionDep,
) -> DocumentCategoryResponse:
    """Get category by ID"""
    repo = DocumentCategoryRepository(db)
    category = await repo.get_by_id(id, user.tenant_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
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


@router.put("/categories/{id}", response_model=DocumentCategoryResponse)
async def update_category(
    id: UUID,
    request: DocumentCategoryUpdate,
    user: UserDep,
    db: SessionDep,
) -> DocumentCategoryResponse:
    """Update a category"""
    try:
        handler = UpdateCategoryHandler(db)
        cmd = UpdateCategoryCommand(
            tenant_id=user.tenant_id,
            category_id=id,
            name=request.name,
            description=request.description,
            color_code=request.color_code,
            icon=request.icon,
            parent_category_id=request.parent_category_id,
            sort_order=request.sort_order,
            is_active=request.is_active,
        )
        return await handler.handle(cmd)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/categories/{id}")
async def delete_category(
    id: UUID,
    user: UserDep,
    db: SessionDep,
) -> dict:
    """Delete a category"""
    try:
        handler = DeleteCategoryHandler(db)
        cmd = DeleteCategoryCommand(tenant_id=user.tenant_id, category_id=id)
        success = await handler.handle(cmd)
        if not success:
            raise HTTPException(status_code=404, detail="Category not found")
        return {"deleted": True}
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.post("/categories/{id}/restore")
async def restore_category(
    id: UUID,
    user: UserDep,
    db: SessionDep,
) -> dict:
    """Restore a soft-deleted category"""
    handler = RestoreCategoryHandler(db)
    cmd = RestoreCategoryCommand(tenant_id=user.tenant_id, category_id=id)
    success = await handler.handle(cmd)
    if not success:
        raise HTTPException(status_code=404, detail="Category not found")
    return {"restored": True}


@router.post("/types", response_model=DocumentTypeResponse)
async def create_document_type(
    request: DocumentTypeCreate,
    user: UserDep,
    db: SessionDep,
) -> DocumentTypeResponse:
    """Create a new document type"""
    try:
        handler = CreateDocumentTypeHandler(db)
        cmd = CreateDocumentTypeCommand(
            tenant_id=user.tenant_id,
            category_id=request.category_id,
            name=request.name,
            description=request.description,
            file_extensions=request.file_extensions,
            max_file_size=request.max_file_size,
            retention_days=request.retention_days,
            custom_attributes=request.custom_attributes,
        )
        return await handler.handle(cmd)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/types", response_model=list[DocumentTypeResponse])
async def list_document_types(
    category_id: Optional[UUID] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    user: UserDep = None,
    db: SessionDep = None,
) -> list[DocumentTypeResponse]:
    """List document types"""
    repo = DocumentTypeRepository(db)
    if category_id:
        types = await repo.list_by_category(category_id, user.tenant_id)
    else:
        types = await repo.list_by_tenant(user.tenant_id, skip, limit)
    return [
        DocumentTypeResponse(
            id=t.id,
            tenant_id=t.tenant_id,
            name=t.name,
            description=t.description,
            category_id=t.category_id,
            file_extensions=t.file_extensions,
            max_file_size=t.max_file_size,
            retention_days=t.retention_days,
            custom_attributes=t.custom_attributes,
            is_active=t.is_active,
            deleted_at=t.deleted_at.isoformat() if t.deleted_at else None,
        )
        for t in types
    ]


@router.get("/types/{id}", response_model=DocumentTypeResponse)
async def get_document_type(
    id: UUID,
    user: UserDep,
    db: SessionDep,
) -> DocumentTypeResponse:
    """Get document type by ID"""
    repo = DocumentTypeRepository(db)
    doc_type = await repo.get_by_id(id, user.tenant_id)
    if not doc_type:
        raise HTTPException(status_code=404, detail="Document type not found")
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


@router.put("/types/{id}", response_model=DocumentTypeResponse)
async def update_document_type(
    id: UUID,
    request: DocumentTypeUpdate,
    user: UserDep,
    db: SessionDep,
) -> DocumentTypeResponse:
    """Update a document type"""
    try:
        handler = UpdateDocumentTypeHandler(db)
        cmd = UpdateDocumentTypeCommand(
            tenant_id=user.tenant_id,
            type_id=id,
            name=request.name,
            description=request.description,
            category_id=request.category_id,
            file_extensions=request.file_extensions,
            max_file_size=request.max_file_size,
            retention_days=request.retention_days,
            custom_attributes=request.custom_attributes,
            is_active=request.is_active,
        )
        return await handler.handle(cmd)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/types/{id}")
async def delete_document_type(
    id: UUID,
    user: UserDep,
    db: SessionDep,
) -> dict:
    """Delete a document type"""
    try:
        handler = DeleteDocumentTypeHandler(db)
        cmd = DeleteDocumentTypeCommand(tenant_id=user.tenant_id, type_id=id)
        success = await handler.handle(cmd)
        if not success:
            raise HTTPException(status_code=404, detail="Document type not found")
        return {"deleted": True}
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.post("/types/{id}/restore")
async def restore_document_type(
    id: UUID,
    user: UserDep,
    db: SessionDep,
) -> dict:
    """Restore a soft-deleted document type"""
    handler = RestoreDocumentTypeHandler(db)
    cmd = RestoreDocumentTypeCommand(tenant_id=user.tenant_id, type_id=id)
    success = await handler.handle(cmd)
    if not success:
        raise HTTPException(status_code=404, detail="Document type not found")
    return {"restored": True}


@router.get("/types/{id}/schema", response_model=AttributeSchemaResponse)
async def get_document_type_schema(
    id: UUID,
    user: UserDep,
    db: SessionDep,
) -> AttributeSchemaResponse:
    """Get custom attributes schema for document type"""
    repo = DocumentTypeRepository(db)
    doc_type = await repo.get_by_id(id, user.tenant_id)
    if not doc_type:
        raise HTTPException(status_code=404, detail="Document type not found")
    return AttributeSchemaResponse(attributes=doc_type.custom_attributes)


# ============= Version History Endpoints =============


@router.get("/versions/{entity_id}", response_model=list[MasterDataVersionResponse])
async def get_version_history(
    entity_id: UUID,
    user: UserDep,
    db: SessionDep,
) -> list[MasterDataVersionResponse]:
    """Get complete version history for entity"""
    service = MasterDataService(db)
    versions = await service.get_version_history(entity_id, user.tenant_id)
    return [
        MasterDataVersionResponse(
            id=v.id,
            tenant_id=v.tenant_id,
            entity_type=v.entity_type,
            entity_id=v.entity_id,
            version_number=v.version_number,
            entity_name=v.entity_name,
            action=v.action,
            previous_values=v.previous_values,
            new_values=v.new_values,
            changed_fields=v.changed_fields,
            changed_by=v.changed_by,
            change_reason=v.change_reason,
            created_at=v.created_at.isoformat(),
        )
        for v in versions
    ]


@router.get("/versions/{entity_id}/{version_number}", response_model=MasterDataVersionResponse)
async def get_specific_version(
    entity_id: UUID,
    version_number: int,
    user: UserDep = None,
    db: SessionDep = None,
) -> MasterDataVersionResponse:
    """Get specific version of entity"""
    service = MasterDataService(db)
    version = await service.get_version(entity_id, version_number, user.tenant_id)
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    return MasterDataVersionResponse(
        id=version.id,
        tenant_id=version.tenant_id,
        entity_type=version.entity_type,
        entity_id=version.entity_id,
        version_number=version.version_number,
        entity_name=version.entity_name,
        action=version.action,
        previous_values=version.previous_values,
        new_values=version.new_values,
        changed_fields=version.changed_fields,
        changed_by=version.changed_by,
        change_reason=version.change_reason,
        created_at=version.created_at.isoformat(),
    )


@router.post("/versions/{entity_id}/{version_number}/rollback")
async def rollback_to_version(
    entity_id: UUID,
    version_number: int,
    user: UserDep = None,
    db: SessionDep = None,
) -> dict:
    """Rollback entity to previous version"""
    try:
        service = MasterDataService(db)
        result = await service.rollback_to_version(
            entity_id=entity_id,
            version_number=version_number,
            tenant_id=user.tenant_id,
            user_id=user.user_id,
        )
        return {"rolled_back": True, "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
