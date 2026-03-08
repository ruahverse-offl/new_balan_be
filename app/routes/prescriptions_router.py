"""
Prescriptions Router
FastAPI routes for prescriptions resource
"""

from typing import Optional
from uuid import UUID
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query, UploadFile, File
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_connection import get_db
from app.services.prescriptions_service import PrescriptionsService
from app.schemas.prescriptions_schema import (
    PrescriptionCreateRequest,
    PrescriptionUpdateRequest,
    PrescriptionResponse,
    PrescriptionListResponse
)
from app.utils.auth import get_current_user_id
from app.utils.rbac import require_permission
from app.utils.request_utils import get_client_ip
from app.utils.storage import StorageService
from app.config import settings

router = APIRouter(prefix="/api/v1/prescriptions", tags=["prescriptions"])


@router.post("/upload", status_code=status.HTTP_201_CREATED, response_model=PrescriptionResponse)
async def upload_prescription(
    file: UploadFile = File(...),
    customer_id: Optional[UUID] = Query(None, description="Customer ID"),
    order_id: Optional[UUID] = Query(None, description="Order ID (if linked to order)"),
    request: Request = None,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id)
):
    """
    Upload a prescription file.
    Requires authentication (any logged-in user can upload prescriptions).
    """
    # Validate file type
    valid_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp', 'application/pdf']
    if file.content_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed types: {', '.join(valid_types)}"
        )
    
    # Validate file size (max 5MB)
    max_size = 5 * 1024 * 1024  # 5MB
    file_content = await file.read()
    await file.seek(0)  # Reset file pointer
    
    if len(file_content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds maximum allowed size (5MB)"
        )
    
    # Save file to storage
    storage_service = StorageService()
    file_info = await storage_service.save_file(file, subdirectory="prescriptions")
    
    # Create prescription record
    ip_address = get_client_ip(request) if request else "unknown"
    prescription_data = PrescriptionCreateRequest(
        customer_id=customer_id or current_user_id,
        order_id=order_id,
        file_url=file_info["file_url"],
        file_name=file_info["file_name"],
        file_size=file_info["file_size"],
        file_type=file_info["file_type"]
    )
    
    service = PrescriptionsService(db)
    prescription = await service.create_prescription(prescription_data, current_user_id, ip_address)
    return prescription


@router.get("/{prescription_id}", response_model=PrescriptionResponse)
async def get_prescription_by_id(
    prescription_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id)
):
    """Get prescription by ID. Requires authentication."""
    service = PrescriptionsService(db)
    prescription = await service.get_prescription_by_id(prescription_id)
    if not prescription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prescription with ID {prescription_id} not found"
        )
    return prescription


@router.get("/{prescription_id}/download")
async def download_prescription_file(
    prescription_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id)
):
    """Download prescription file. Requires authentication."""
    service = PrescriptionsService(db)
    prescription = await service.get_prescription_by_id(prescription_id)
    if not prescription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prescription with ID {prescription_id} not found"
        )

    file_url = prescription.file_url
    # Local storage: file_url is like /storage/prescriptions/uuid.jpg
    if file_url.startswith("/storage/"):
        local_path = Path(settings.LOCAL_STORAGE_PATH) / file_url.replace("/storage/", "", 1)
        if not local_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prescription file not found on disk"
            )
        return FileResponse(
            path=str(local_path),
            filename=prescription.file_name,
            media_type=prescription.file_type or "application/octet-stream"
        )
    else:
        # Azure or external URL - redirect
        return RedirectResponse(url=file_url)


@router.get("", response_model=PrescriptionListResponse)
@router.get("/", response_model=PrescriptionListResponse)
async def get_prescriptions_list(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    search: Optional[str] = Query(default=None),
    sort_by: Optional[str] = Query(default="created_at"),
    sort_order: Optional[str] = Query(default="desc", pattern="^(asc|desc)$"),
    status: Optional[str] = Query(default=None, description="Filter by status (PENDING, APPROVED, REJECTED)"),
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id)
):
    """
    Get list of prescriptions. Requires authentication.
    Pharmacists can view all prescriptions, customers can view their own.
    """
    service = PrescriptionsService(db)
    result = await service.get_prescriptions_list(
        limit=limit, offset=offset, search=search, sort_by=sort_by, sort_order=sort_order, status=status
    )
    return result


@router.post("/{prescription_id}/approve", response_model=PrescriptionResponse)
async def approve_prescription(
    prescription_id: UUID,
    notes: Optional[str] = Query(None, description="Approval notes"),
    request: Request = None,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(require_permission("PRESCRIPTION_APPROVE"))
):
    """
    Approve a prescription. Requires PRESCRIPTION_APPROVE permission (Pharmacist role).
    """
    ip_address = get_client_ip(request) if request else "unknown"
    service = PrescriptionsService(db)
    prescription = await service.approve_prescription(prescription_id, current_user_id, notes, ip_address)
    if not prescription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prescription with ID {prescription_id} not found"
        )
    return prescription


@router.post("/{prescription_id}/reject", response_model=PrescriptionResponse)
async def reject_prescription(
    prescription_id: UUID,
    rejection_reason: str = Query(..., description="Reason for rejection"),
    request: Request = None,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(require_permission("PRESCRIPTION_APPROVE"))
):
    """
    Reject a prescription. Requires PRESCRIPTION_APPROVE permission (Pharmacist role).
    """
    ip_address = get_client_ip(request) if request else "unknown"
    service = PrescriptionsService(db)
    prescription = await service.reject_prescription(prescription_id, current_user_id, rejection_reason, ip_address)
    if not prescription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prescription with ID {prescription_id} not found"
        )
    return prescription


@router.patch("/{prescription_id}", response_model=PrescriptionResponse)
async def update_prescription(
    prescription_id: UUID,
    data: PrescriptionUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(require_permission("PRESCRIPTION_REVIEW"))
):
    """Update a prescription. Requires PRESCRIPTION_REVIEW permission."""
    ip_address = get_client_ip(request)
    service = PrescriptionsService(db)
    prescription = await service.update_prescription(prescription_id, data, current_user_id, ip_address)
    if not prescription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prescription with ID {prescription_id} not found"
        )
    return prescription


@router.delete("/{prescription_id}", status_code=status.HTTP_200_OK)
async def delete_prescription(
    prescription_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id)
):
    """Soft delete a prescription. Requires authentication."""
    ip_address = get_client_ip(request)
    service = PrescriptionsService(db)
    deleted = await service.delete_prescription(prescription_id, current_user_id, ip_address)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prescription with ID {prescription_id} not found"
        )
    return {"message": "Prescription deleted successfully", "id": str(prescription_id)}
