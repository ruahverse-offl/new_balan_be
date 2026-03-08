"""
Addresses Router
FastAPI routes for user addresses
"""

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_connection import get_db
from app.services.addresses_service import AddressesService
from app.schemas.addresses_schema import (
    AddressCreateRequest,
    AddressUpdateRequest,
    AddressResponse,
)
from app.utils.auth import get_current_user_id
from app.utils.request_utils import get_client_ip

router = APIRouter(prefix="/api/v1/addresses", tags=["addresses"])


@router.get("/my-addresses", response_model=List[AddressResponse])
async def get_my_addresses(
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id)
):
    """Get all addresses for the current user."""
    service = AddressesService(db)
    return await service.get_my_addresses(current_user_id)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=AddressResponse)
async def create_address(
    data: AddressCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id)
):
    """Create a new address for the current user."""
    ip_address = get_client_ip(request)
    service = AddressesService(db)
    return await service.create_address(data, current_user_id, ip_address)


@router.patch("/{address_id}", response_model=AddressResponse)
async def update_address(
    address_id: UUID,
    data: AddressUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id)
):
    """Update an address (must be owned by current user)."""
    ip_address = get_client_ip(request)
    service = AddressesService(db)
    address = await service.update_address(address_id, data, current_user_id, ip_address)
    if not address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Address not found or not owned by you"
        )
    return address


@router.delete("/{address_id}", status_code=status.HTTP_200_OK)
async def delete_address(
    address_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id)
):
    """Soft delete an address (must be owned by current user)."""
    ip_address = get_client_ip(request)
    service = AddressesService(db)
    deleted = await service.delete_address(address_id, current_user_id, ip_address)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Address not found or not owned by you"
        )
    return {"message": "Address deleted successfully", "id": str(address_id)}


@router.patch("/{address_id}/default", response_model=AddressResponse)
async def set_default_address(
    address_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id)
):
    """Set an address as the default (must be owned by current user)."""
    ip_address = get_client_ip(request)
    service = AddressesService(db)
    address = await service.set_default(address_id, current_user_id, ip_address)
    if not address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Address not found or not owned by you"
        )
    return address
