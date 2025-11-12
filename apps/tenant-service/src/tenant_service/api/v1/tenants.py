"""Tenant REST API endpoints."""

import logging
from typing import List

from fastapi import APIRouter, status

from tenant_service.api.dependencies import SessionDep, UserDep
from tenant_service.application.handlers.tenant_handler import (
    CreateTenantCommand,
    CreateTenantHandler,
    DeleteTenantCommand,
    DeleteTenantHandler,
    UpdateTenantCommand,
    UpdateTenantHandler,
)
from tenant_service.domain.services.tenant_service import TenantService
from tenant_service.infrastructure.models.tenant import TenantCreate, TenantResponse, TenantUpdate
from tenant_service.infrastructure.repositories.tenant_repository import TenantRepository
from tenant_service.logging import set_tenant_context, set_user_context

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/tenants", tags=["tenants"])


@router.post("", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    tenant_data: TenantCreate,
    user: UserDep,
    session: SessionDep,
):
    """
    Create a new tenant.

    **Permission**: TENANT_CREATE (System Admin only)

    Args:
        tenant_data: Tenant creation data
        user: Authenticated user context
        session: Database session

    Returns:
        Created tenant response
    """
    # Set logging context
    set_user_context(user.user_id)

    # Create handler
    repository = TenantRepository(session)
    service = TenantService(repository)
    handler = CreateTenantHandler(service)

    # Create command and handle
    command = CreateTenantCommand(
        name=tenant_data.name,
        display_name=tenant_data.display_name,
        description=tenant_data.description,
        subscription_plan=tenant_data.subscription_plan.value,
        admin_email=tenant_data.admin_email,
    )

    tenant = await handler.handle(command)
    set_tenant_context(tenant.id)

    logger.info(f"Tenant created: {tenant.id}")
    return TenantResponse.from_orm(tenant)


@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: str,
    user: UserDep,
    session: SessionDep,
):
    """
    Get tenant by ID with isolation verification.

    **Permission**: TENANT_READ

    Args:
        tenant_id: Tenant identifier
        user: Authenticated user context
        session: Database session

    Returns:
        Tenant response
    """
    set_user_context(user.user_id)
    set_tenant_context(tenant_id)

    repository = TenantRepository(session)
    service = TenantService(repository)

    # Verify tenant isolation - user can only read their own tenant
    tenant = await service.get_tenant(tenant_id, user_tenant_id=user.tenant_id)

    logger.info(f"Tenant retrieved: {tenant_id}")
    return TenantResponse.from_orm(tenant)


@router.get("", response_model=List[TenantResponse])
async def list_tenants(
    user: UserDep,
    session: SessionDep,
    skip: int = 0,
    limit: int = 100,
):
    """
    List tenants.

    **Permission**: TENANT_READ

    Args:
        user: Authenticated user context
        session: Database session
        skip: Number of records to skip
        limit: Maximum records to return (max 100)

    Returns:
        List of tenant responses
    """
    set_user_context(user.user_id)

    # Ensure limit doesn't exceed maximum
    limit = min(limit, 100)

    repository = TenantRepository(session)
    service = TenantService(repository)

    # Users can only list their own tenant
    tenants = await service.list_tenants(user_tenant_id=user.tenant_id, skip=skip, limit=limit)

    logger.info(f"Tenants listed: {len(tenants)} records")
    return [TenantResponse.from_orm(t) for t in tenants]


@router.put("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: str,
    tenant_data: TenantUpdate,
    user: UserDep,
    session: SessionDep,
):
    """
    Update tenant by ID.

    **Permission**: TENANT_UPDATE (Tenant Admin)

    Args:
        tenant_id: Tenant identifier
        tenant_data: Update data
        user: Authenticated user context
        session: Database session

    Returns:
        Updated tenant response
    """
    set_user_context(user.user_id)
    set_tenant_context(tenant_id)

    # Create handler
    repository = TenantRepository(session)
    service = TenantService(repository)
    handler = UpdateTenantHandler(service)

    # Create command
    command = UpdateTenantCommand(
        tenant_id=tenant_id,
        display_name=tenant_data.display_name,
        description=tenant_data.description,
        subscription_plan=tenant_data.subscription_plan.value if tenant_data.subscription_plan else None,
        is_active=tenant_data.is_active,
        admin_email=tenant_data.admin_email,
        user_tenant_id=user.tenant_id,
    )

    tenant = await handler.handle(command)

    logger.info(f"Tenant updated: {tenant_id}")
    return TenantResponse.from_orm(tenant)


@router.delete("/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tenant(
    tenant_id: str,
    user: UserDep,
    session: SessionDep,
):
    """
    Delete tenant (soft delete).

    **Permission**: TENANT_DELETE (System Admin only)

    Args:
        tenant_id: Tenant identifier
        user: Authenticated user context
        session: Database session
    """
    set_user_context(user.user_id)
    set_tenant_context(tenant_id)

    # Create handler
    repository = TenantRepository(session)
    service = TenantService(repository)
    handler = DeleteTenantHandler(service)

    # Create command
    command = DeleteTenantCommand(
        tenant_id=tenant_id,
        user_tenant_id=user.tenant_id,
    )

    await handler.handle(command)

    logger.info(f"Tenant deleted: {tenant_id}")
