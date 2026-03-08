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
    InsuranceEnquiryListResponse
)
from app.utils.auth import get_current_user_id_optional
from app.utils.rbac import require_permission
from app.utils.request_utils import get_client_ip

router = APIRouter(prefix="/api/v1/insurance-enquiries", tags=["insurance-enquiries"])


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=InsuranceEnquiryResponse)
async def create_insurance_enquiry(
    data: InsuranceEnquiryCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: Optional[UUID] = Depends(get_current_user_id_optional)
):
    """Create a new insurance enquiry (public - customers can submit)."""
    user_id = current_user_id or UUID("00000000-0000-0000-0000-000000000000")
    ip_address = get_client_ip(request)
    service = InsuranceEnquiriesService(db)
    enquiry = await service.create_insurance_enquiry(data, user_id, ip_address)
    return enquiry


@router.get("/{enquiry_id}", response_model=InsuranceEnquiryResponse)
async def get_insurance_enquiry_by_id(
    enquiry_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get insurance enquiry by ID."""
    service = InsuranceEnquiriesService(db)
    enquiry = await service.get_insurance_enquiry_by_id(enquiry_id)
    if not enquiry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Insurance enquiry with ID {enquiry_id} not found"
        )
    return enquiry


@router.get("/", response_model=InsuranceEnquiryListResponse)
async def get_insurance_enquiries_list(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    search: Optional[str] = Query(default=None),
    sort_by: Optional[str] = Query(default="created_at"),
    sort_order: Optional[str] = Query(default="desc", pattern="^(asc|desc)$"),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    db: AsyncSession = Depends(get_db)
):
    """Get list of insurance enquiries with pagination, search, and sort."""
    service = InsuranceEnquiriesService(db)
    result = await service.get_insurance_enquiries_list(
        limit=limit, offset=offset, search=search, sort_by=sort_by, sort_order=sort_order,
        status=status_filter
    )
    return result


@router.patch("/{enquiry_id}", response_model=InsuranceEnquiryResponse)
async def update_insurance_enquiry(
    enquiry_id: UUID,
    data: InsuranceEnquiryUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(require_permission("APPOINTMENT_UPDATE"))
):
    """Update an insurance enquiry (admin only)."""
    ip_address = get_client_ip(request)
    service = InsuranceEnquiriesService(db)
    enquiry = await service.update_insurance_enquiry(enquiry_id, data, current_user_id, ip_address)
    if not enquiry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Insurance enquiry with ID {enquiry_id} not found"
        )
    return enquiry


@router.delete("/{enquiry_id}", status_code=status.HTTP_200_OK)
async def delete_insurance_enquiry(
    enquiry_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(require_permission("APPOINTMENT_DELETE"))
):
    """Soft delete an insurance enquiry (admin only)."""
    ip_address = get_client_ip(request)
    service = InsuranceEnquiriesService(db)
    deleted = await service.delete_insurance_enquiry(enquiry_id, current_user_id, ip_address)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Insurance enquiry with ID {enquiry_id} not found"
        )
    return {"message": "Insurance enquiry deleted successfully", "id": str(enquiry_id)}
