"""
Pharmacist Profiles Router
FastAPI routes for pharmacist_profiles resource
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_connection import get_db
from app.services.pharmacist_profiles_service import PharmacistProfilesService
from app.schemas.pharmacist_profiles_schema import (
    PharmacistProfileCreateRequest,
    PharmacistProfileUpdateRequest,
    PharmacistProfileResponse,
    PharmacistProfileListResponse
)
from app.utils.rbac import require_permission
from app.utils.request_utils import get_client_ip

router = APIRouter(prefix="/api/v1/pharmacist-profiles", tags=["pharmacist-profiles"])


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=PharmacistProfileResponse)
async def create_pharmacist_profile(
    data: PharmacistProfileCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(require_permission("STAFF_CREATE"))
):
    """Create a new pharmacist profile. Requires STAFF_CREATE permission."""
    ip_address = get_client_ip(request)
    service = PharmacistProfilesService(db)
    profile = await service.create_pharmacist_profile(data, current_user_id, ip_address)
    return profile


@router.get("/{user_id}", response_model=PharmacistProfileResponse)
async def get_pharmacist_profile_by_id(
    user_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get pharmacist profile by user ID."""
    service = PharmacistProfilesService(db)
    profile = await service.get_pharmacist_profile_by_id(user_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pharmacist profile with user ID {user_id} not found"
        )
    return profile


@router.get("/", response_model=PharmacistProfileListResponse)
async def get_pharmacist_profiles_list(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    search: Optional[str] = Query(default=None),
    sort_by: Optional[str] = Query(default="created_at"),
    sort_order: Optional[str] = Query(default="desc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db)
):
    """Get list of pharmacist profiles with pagination, search, and sort."""
    service = PharmacistProfilesService(db)
    result = await service.get_pharmacist_profiles_list(
        limit=limit, offset=offset, search=search, sort_by=sort_by, sort_order=sort_order
    )
    return result


@router.patch("/{user_id}", response_model=PharmacistProfileResponse)
async def update_pharmacist_profile(
    user_id: UUID,
    data: PharmacistProfileUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(require_permission("STAFF_UPDATE"))
):
    """Update a pharmacist profile. Requires STAFF_UPDATE permission."""
    ip_address = get_client_ip(request)
    service = PharmacistProfilesService(db)
    profile = await service.update_pharmacist_profile(user_id, data, current_user_id, ip_address)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pharmacist profile with user ID {user_id} not found"
        )
    return profile


@router.delete("/{user_id}", status_code=status.HTTP_200_OK)
async def delete_pharmacist_profile(
    user_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(require_permission("STAFF_DELETE"))
):
    """Soft delete a pharmacist profile. Requires STAFF_DELETE permission."""
    ip_address = get_client_ip(request)
    service = PharmacistProfilesService(db)
    deleted = await service.delete_pharmacist_profile(user_id, current_user_id, ip_address)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pharmacist profile with user ID {user_id} not found"
        )
    return {"message": "Pharmacist profile deleted successfully", "id": str(user_id)}
