"""
Insurance Enquiries Router
FastAPI routes for insurance_enquiries resource
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_connection import get_db
from app.services.insurance_enquiries_service import InsuranceEnquiriesService
from app.schemas.insurance_enquiries_schema import (
    InsuranceEnquiryCreateRequest,
    InsuranceEnquiryUpdateRequest,
    InsuranceEnquiryResponse,
    InsuranceEnquiryListResponse,
)
from app.utils.auth import get_current_user_id_optional
from app.utils.rbac import require_module_action
from app.utils.request_utils import get_client_ip

router = APIRouter(prefix="/api/v1/insurance-enquiries", tags=["insurance-enquiries"])

_ANON = UUID("00000000-0000-0000-0000-000000000000")


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=InsuranceEnquiryResponse)
async def create_enquiry(
    data: InsuranceEnquiryCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: Optional[UUID] = Depends(get_current_user_id_optional),
):
    """Submit an insurance enquiry. No authentication required."""
    user_id = current_user_id or _ANON
    ip = get_client_ip(request)
    service = InsuranceEnquiriesService(db)
    enquiry = await service.create_enquiry(data, user_id, ip)
    await db.commit()
    return enquiry


@router.get("/", response_model=InsuranceEnquiryListResponse)
async def list_enquiries(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    search: Optional[str] = Query(default=None),
    sort_by: Optional[str] = Query(default="created_at"),
    sort_order: Optional[str] = Query(default="desc", pattern="^(asc|desc)$"),
    status: Optional[str] = Query(default=None, description="Filter by status"),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(require_module_action("appointments", "read")),
):
    """List all insurance enquiries. Requires appointments:read."""
    service = InsuranceEnquiriesService(db)
    return await service.get_enquiries_list(
        limit=limit,
        offset=offset,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        status=status,
    )


@router.get("/{enquiry_id}", response_model=InsuranceEnquiryResponse)
async def get_enquiry(
    enquiry_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(require_module_action("appointments", "read")),
):
    """Get a single insurance enquiry by ID. Requires appointments:read."""
    service = InsuranceEnquiriesService(db)
    e = await service.get_enquiry_by_id(enquiry_id)
    if not e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Insurance enquiry {enquiry_id} not found",
        )
    return e


@router.patch("/{enquiry_id}", response_model=InsuranceEnquiryResponse)
async def update_enquiry(
    enquiry_id: UUID,
    data: InsuranceEnquiryUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(require_module_action("appointments", "update")),
):
    """Update status / notes on an enquiry. Requires appointments:update."""
    ip = get_client_ip(request)
    service = InsuranceEnquiriesService(db)
    e = await service.update_enquiry(enquiry_id, data, current_user_id, ip)
    if not e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Insurance enquiry {enquiry_id} not found",
        )
    await db.commit()
    return e


@router.delete("/{enquiry_id}", status_code=status.HTTP_200_OK)
async def delete_enquiry(
    enquiry_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(require_module_action("appointments", "delete")),
):
    """Soft-delete an insurance enquiry. Requires appointments:delete."""
    ip = get_client_ip(request)
    service = InsuranceEnquiriesService(db)
    deleted = await service.delete_enquiry(enquiry_id, current_user_id, ip)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Insurance enquiry {enquiry_id} not found",
        )
    return {"message": "Insurance enquiry deleted", "id": str(enquiry_id)}
