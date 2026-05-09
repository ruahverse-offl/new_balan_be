"""
Users Router
FastAPI routes for users resource
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_connection import get_db
from app.services.users_service import UsersService
from app.schemas.users_schema import (
    UserCreateRequest,
    UserUpdateRequest,
    UserResponse,
    UserListResponse,
    DeliveryAgentListResponse,
)
from app.utils.auth import get_current_user_id_optional
from app.utils.request_utils import get_client_ip
from app.utils.rbac import require_module_action

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=UserResponse)
async def create_user(
    data: UserCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: Optional[UUID] = Depends(get_current_user_id_optional)
):
    """Create a new user."""
    user_id = current_user_id or UUID("00000000-0000-0000-0000-000000000000")
    ip_address = get_client_ip(request)
    service = UsersService(db)
    user = await service.create_user(data, user_id, ip_address)
    return user


@router.get("/delivery-agents", response_model=DeliveryAgentListResponse)
async def list_delivery_agents_for_assignment(
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(require_module_action("orders", "update")),
):
    """
    Users whose role includes DELIVERY_ORDER_UPDATE — for assign-delivery UI.
    Includes name, phone, and a short workload status.
    """
    service = UsersService(db)
    return await service.list_delivery_agents_for_assignment()


@router.get("/customers", response_model=UserListResponse)
async def get_customers_list(
    limit: int = Query(default=20, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    search: Optional[str] = Query(default=None),
    sort_by: Optional[str] = Query(default="created_at"),
    sort_order: Optional[str] = Query(default="desc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(require_module_action("customers", "read")),
):
    """List all customer accounts (CUSTOMER + PUBLIC roles). Requires customers:read."""
    service = UsersService(db)
    return await service.get_customers_list(
        limit=limit, offset=offset, search=search, sort_by=sort_by, sort_order=sort_order
    )


@router.get("/", response_model=UserListResponse)
async def get_users_list(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    search: Optional[str] = Query(default=None),
    sort_by: Optional[str] = Query(default="created_at"),
    sort_order: Optional[str] = Query(default="desc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db)
):
    """Get list of users with pagination, search, and sort."""
    service = UsersService(db)
    result = await service.get_users_list(
        limit=limit, offset=offset, search=search, sort_by=sort_by, sort_order=sort_order
    )
    return result


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get user by ID."""
    service = UsersService(db)
    user = await service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    return user


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    data: UserUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: Optional[UUID] = Depends(get_current_user_id_optional)
):
    """Update a user."""
    current_user = current_user_id or UUID("00000000-0000-0000-0000-000000000000")
    ip_address = get_client_ip(request)
    service = UsersService(db)
    user = await service.update_user(user_id, data, current_user, ip_address)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    return user


@router.delete("/{user_id}", status_code=status.HTTP_200_OK)
async def delete_user(
    user_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: Optional[UUID] = Depends(get_current_user_id_optional)
):
    """Soft delete a user."""
    current_user = current_user_id or UUID("00000000-0000-0000-0000-000000000000")
    ip_address = get_client_ip(request)
    service = UsersService(db)
    deleted = await service.delete_user(user_id, current_user, ip_address)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    return {"message": "User deleted successfully", "id": str(user_id)}
