"""
Role Permissions Router
FastAPI routes for role_permissions resource
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_connection import get_db
from app.services.role_permissions_service import RolePermissionsService
from app.schemas.role_permissions_schema import (
    RolePermissionCreateRequest,
    RolePermissionUpdateRequest,
    RolePermissionResponse,
    RolePermissionListResponse
)
from app.utils.rbac import require_permission
from app.utils.request_utils import get_client_ip

router = APIRouter(prefix="/api/v1/role-permissions", tags=["role-permissions"])


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=RolePermissionResponse)
async def create_role_permission(
    data: RolePermissionCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(require_permission("ROLE_PERMISSION_CREATE"))
):
    """
    Create a new role permission.

    Requires permission: ROLE_PERMISSION_CREATE
    """
    ip_address = get_client_ip(request)
    service = RolePermissionsService(db)
    role_permission = await service.create_role_permission(data, current_user_id, ip_address)
    return role_permission


@router.get("/{role_permission_id}", response_model=RolePermissionResponse)
async def get_role_permission_by_id(
    role_permission_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(require_permission("ROLE_PERMISSION_VIEW"))
):
    """
    Get role permission by ID.

    Requires permission: ROLE_PERMISSION_VIEW
    """
    service = RolePermissionsService(db)
    role_permission = await service.get_role_permission_by_id(role_permission_id)
    if not role_permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role permission with ID {role_permission_id} not found"
        )
    return role_permission


@router.get("/", response_model=RolePermissionListResponse)
async def get_role_permissions_list(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    search: Optional[str] = Query(default=None),
    sort_by: Optional[str] = Query(default="created_at"),
    sort_order: Optional[str] = Query(default="desc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(require_permission("ROLE_PERMISSION_VIEW"))
):
    """
    Get list of role permissions with pagination, search, and sort.

    Requires permission: ROLE_PERMISSION_VIEW
    """
    service = RolePermissionsService(db)
    result = await service.get_role_permissions_list(
        limit=limit, offset=offset, search=search, sort_by=sort_by, sort_order=sort_order
    )
    return result


@router.patch("/{role_permission_id}", response_model=RolePermissionResponse)
async def update_role_permission(
    role_permission_id: UUID,
    data: RolePermissionUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(require_permission("ROLE_PERMISSION_UPDATE"))
):
    """
    Update a role permission.

    Requires permission: ROLE_PERMISSION_UPDATE
    """
    ip_address = get_client_ip(request)
    service = RolePermissionsService(db)
    role_permission = await service.update_role_permission(role_permission_id, data, current_user_id, ip_address)
    if not role_permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role permission with ID {role_permission_id} not found"
        )
    return role_permission


@router.delete("/{role_permission_id}", status_code=status.HTTP_200_OK)
async def delete_role_permission(
    role_permission_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(require_permission("ROLE_PERMISSION_DELETE"))
):
    """
    Soft delete a role permission.

    Requires permission: ROLE_PERMISSION_DELETE
    """
    ip_address = get_client_ip(request)
    service = RolePermissionsService(db)
    deleted = await service.delete_role_permission(role_permission_id, current_user_id, ip_address)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role permission with ID {role_permission_id} not found"
        )
    return {"message": "Role permission deleted successfully", "id": str(role_permission_id)}
