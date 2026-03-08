"""
Roles Router
FastAPI routes for roles resource
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_connection import get_db
from app.services.roles_service import RolesService
from app.schemas.roles_schema import (
    RoleCreateRequest,
    RoleUpdateRequest,
    RoleResponse,
    RoleListResponse
)
from app.utils.rbac import require_permission
from app.utils.request_utils import get_client_ip
from app.config import get_settings

router = APIRouter(prefix="/api/v1/roles", tags=["roles"])
settings = get_settings()


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=RoleResponse)
async def create_role(
    data: RoleCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(require_permission("ROLE_CREATE"))
):
    """
    Create a new role.

    Requires permission: ROLE_CREATE

    - **name**: Role name (required)
    - **description**: Role description (optional)
    - **is_active**: Whether the role is active (default: true)
    """
    ip_address = get_client_ip(request)

    # Create role
    service = RolesService(db)
    role = await service.create_role(data, current_user_id, ip_address)

    return role


@router.get("/{role_id}", response_model=RoleResponse)
async def get_role_by_id(
    role_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(require_permission("ROLE_VIEW"))
):
    """
    Get role by ID.

    Requires permission: ROLE_VIEW

    - **role_id**: Role UUID
    """
    service = RolesService(db)
    role = await service.get_role_by_id(role_id)

    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role with ID {role_id} not found"
        )

    return role


@router.get("/", response_model=RoleListResponse)
async def get_roles_list(
    limit: int = Query(default=20, ge=1, le=100, description="Number of records per page"),
    offset: int = Query(default=0, ge=0, description="Number of records to skip"),
    search: Optional[str] = Query(default=None, description="Search term"),
    sort_by: Optional[str] = Query(default="created_at", description="Field to sort by"),
    sort_order: Optional[str] = Query(default="desc", pattern="^(asc|desc)$", description="Sort order"),
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(require_permission("ROLE_VIEW"))
):
    """
    Get list of roles with pagination, search, and sort.

    Requires permission: ROLE_VIEW

    - **limit**: Number of records per page (1-100, default: 20)
    - **offset**: Number of records to skip (default: 0)
    - **search**: Search term to match against name and description
    - **sort_by**: Field name to sort by (default: created_at)
    - **sort_order**: Sort order - 'asc' or 'desc' (default: desc)
    """
    service = RolesService(db)
    result = await service.get_roles_list(
        limit=limit,
        offset=offset,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order
    )

    return result


@router.patch("/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: UUID,
    data: RoleUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(require_permission("ROLE_UPDATE"))
):
    """
    Update a role.

    Requires permission: ROLE_UPDATE

    - **role_id**: Role UUID
    - All fields are optional - only provided fields will be updated
    """
    ip_address = get_client_ip(request)

    # Update role
    service = RolesService(db)
    role = await service.update_role(role_id, data, current_user_id, ip_address)

    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role with ID {role_id} not found"
        )

    return role


@router.delete("/{role_id}", status_code=status.HTTP_200_OK)
async def delete_role(
    role_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(require_permission("ROLE_DELETE"))
):
    """
    Soft delete a role.

    Requires permission: ROLE_DELETE

    - **role_id**: Role UUID
    - Sets is_deleted = True (does not physically delete)
    """
    ip_address = get_client_ip(request)

    # Delete role
    service = RolesService(db)
    deleted = await service.delete_role(role_id, current_user_id, ip_address)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role with ID {role_id} not found"
        )

    return {"message": "Role deleted successfully", "id": str(role_id)}
