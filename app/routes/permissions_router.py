"""
Permissions Router
FastAPI routes for permissions resource
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_connection import get_db
from app.services.permissions_service import PermissionsService
from app.schemas.permissions_schema import (
    PermissionCreateRequest,
    PermissionUpdateRequest,
    PermissionResponse,
    PermissionListResponse
)
from app.utils.rbac import require_permission
from app.utils.request_utils import get_client_ip

router = APIRouter(prefix="/api/v1/permissions", tags=["permissions"])


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=PermissionResponse)
async def create_permission(
    data: PermissionCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(require_permission("PERMISSION_CREATE"))
):
    """
    Create a new permission.

    Requires permission: PERMISSION_CREATE
    """
    ip_address = get_client_ip(request)
    service = PermissionsService(db)
    permission = await service.create_permission(data, current_user_id, ip_address)
    return permission


@router.get("/{permission_id}", response_model=PermissionResponse)
async def get_permission_by_id(
    permission_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(require_permission("PERMISSION_VIEW"))
):
    """
    Get permission by ID.

    Requires permission: PERMISSION_VIEW
    """
    service = PermissionsService(db)
    permission = await service.get_permission_by_id(permission_id)
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Permission with ID {permission_id} not found"
        )
    return permission


@router.get("/", response_model=PermissionListResponse)
async def get_permissions_list(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    search: Optional[str] = Query(default=None),
    sort_by: Optional[str] = Query(default="created_at"),
    sort_order: Optional[str] = Query(default="desc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(require_permission("PERMISSION_VIEW"))
):
    """
    Get list of permissions with pagination, search, and sort.

    Requires permission: PERMISSION_VIEW
    """
    service = PermissionsService(db)
    result = await service.get_permissions_list(
        limit=limit, offset=offset, search=search, sort_by=sort_by, sort_order=sort_order
    )
    return result


@router.patch("/{permission_id}", response_model=PermissionResponse)
async def update_permission(
    permission_id: UUID,
    data: PermissionUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(require_permission("PERMISSION_UPDATE"))
):
    """
    Update a permission.

    Requires permission: PERMISSION_UPDATE
    """
    ip_address = get_client_ip(request)
    service = PermissionsService(db)
    permission = await service.update_permission(permission_id, data, current_user_id, ip_address)
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Permission with ID {permission_id} not found"
        )
    return permission


@router.delete("/{permission_id}", status_code=status.HTTP_200_OK)
async def delete_permission(
    permission_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(require_permission("PERMISSION_DELETE"))
):
    """
    Soft delete a permission.

    Requires permission: PERMISSION_DELETE
    """
    ip_address = get_client_ip(request)
    service = PermissionsService(db)
    deleted = await service.delete_permission(permission_id, current_user_id, ip_address)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Permission with ID {permission_id} not found"
        )
    return {"message": "Permission deleted successfully", "id": str(permission_id)}
