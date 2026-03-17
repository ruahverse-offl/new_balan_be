"""
Prescriptions Router
FastAPI routes for prescriptions resource
"""

from typing import Optional
from uuid import UUID, uuid4
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query, UploadFile, File
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_connection import get_db
from app.services.prescriptions_service import PrescriptionsService
from app.schemas.prescriptions_schema import (
    PrescriptionUpdateRequest,
    PrescriptionResponse,
    PrescriptionListResponse
)
from app.utils.auth import get_current_user_id
from app.utils.rbac import require_permission
from app.utils.request_utils import get_client_ip
from app.utils.storage import StorageService
from app.utils.prescription_local_storage import (
    save_prescription_to_manifest,
    get_prescription_from_manifest,
)
from app.config import settings
from datetime import datetime

router = APIRouter(prefix="/api/v1/prescriptions", tags=["prescriptions"])

def _sniff_mime_from_bytes(b: bytes) -> Optional[str]:
    """Best-effort MIME sniffing using magic bytes (no external deps)."""
    if not b:
        return None
    if b.startswith(b"%PDF-"):
        return "application/pdf"
    if b.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if b.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if b.startswith(b"RIFF") and b[8:12] == b"WEBP":
        return "image/webp"
    return None


def _prescription_response_from_manifest(entry_id: str, entry: dict) -> PrescriptionResponse:
    """Build PrescriptionResponse from a local manifest entry."""
    created_at = datetime.fromisoformat(entry["created_at"].replace("Z", "+00:00"))
    return PrescriptionResponse(
        id=UUID(entry_id),
        customer_id=UUID(entry["customer_id"]),
        order_id=UUID(entry["order_id"]) if entry.get("order_id") else None,
        file_url=entry["file_url"],
        file_name=entry["file_name"],
        file_size=entry["file_size"],
        file_type=entry["file_type"],
        status=entry.get("status", "PENDING"),
        reviewed_by=UUID(entry["reviewed_by"]) if entry.get("reviewed_by") else None,
        review_notes=entry.get("review_notes"),
        rejection_reason=entry.get("rejection_reason"),
        created_by=UUID(entry["created_by"]),
        created_at=created_at,
        created_ip=entry["created_ip"],
        updated_by=UUID(entry["updated_by"]) if entry.get("updated_by") else None,
        updated_at=datetime.fromisoformat(entry["updated_at"].replace("Z", "+00:00")) if entry.get("updated_at") else None,
        updated_ip=entry.get("updated_ip"),
        is_deleted=entry.get("is_deleted", False),
    )


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
    Upload a prescription file. File is stored on server (local disk); metadata is saved in the database.
    Requires authentication (any logged-in user can upload prescriptions).
    """
    from app.schemas.prescriptions_schema import PrescriptionCreateRequest

    # Validate file type (declared)
    valid_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp', 'application/pdf']
    if file.content_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed types: {', '.join(valid_types)}"
        )
    
    # Validate file size and sniff MIME from bytes (prevents spoofed content-type)
    max_size = int(settings.MAX_UPLOAD_SIZE or 0) or (10 * 1024 * 1024)
    file_content = await file.read(max_size + 1)
    await file.seek(0)  # Reset file pointer
    
    if len(file_content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum allowed size ({max_size} bytes)"
        )

    sniffed = _sniff_mime_from_bytes(file_content[:16])
    if sniffed:
        declared = (file.content_type or "").lower()
        # Treat image/jpg as image/jpeg
        if declared == "image/jpg":
            declared = "image/jpeg"
        if sniffed != declared:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File content does not match the declared file type.",
            )
    
    # Save file to server (local disk)
    storage_service = StorageService()
    file_info = await storage_service.save_file(file, subdirectory="prescriptions")

    prescription_id = uuid4()
    ip_address = get_client_ip(request) if request else "unknown"
    cid = customer_id or current_user_id

    # Save metadata to database so prescriptions are queryable and linked to orders
    create_data = PrescriptionCreateRequest(
        id=prescription_id,
        customer_id=cid,
        order_id=order_id,
        file_url=file_info["file_url"],
        file_name=file_info["file_name"],
        file_size=file_info["file_size"],
        file_type=file_info["file_type"],
    )
    service = PrescriptionsService(db)
    prescription = await service.create_prescription(create_data, current_user_id, ip_address)

    # Also append to local manifest for backward compatibility (get/download can check manifest first)
    save_prescription_to_manifest(
        storage_base=settings.LOCAL_STORAGE_PATH,
        prescription_id=str(prescription_id),
        customer_id=str(cid),
        file_url=file_info["file_url"],
        file_name=file_info["file_name"],
        file_size=file_info["file_size"],
        file_type=file_info["file_type"],
        created_by=str(current_user_id),
        created_ip=ip_address,
        order_id=str(order_id) if order_id else None,
    )
    return prescription


@router.get("/{prescription_id}", response_model=PrescriptionResponse)
async def get_prescription_by_id(
    prescription_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id)
):
    """Get prescription by ID. DB is source of truth (upload saves to server + DB); manifest fallback for legacy. Requires authentication."""
    service = PrescriptionsService(db)
    prescription = await service.get_prescription_by_id(prescription_id)
    if prescription:
        return prescription
    entry = get_prescription_from_manifest(settings.LOCAL_STORAGE_PATH, str(prescription_id))
    if entry:
        return _prescription_response_from_manifest(str(prescription_id), entry)
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Prescription with ID {prescription_id} not found"
    )


@router.get("/{prescription_id}/download")
async def download_prescription_file(
    prescription_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(get_current_user_id)
):
    """Download prescription file. DB first (upload saves to server + DB); manifest fallback for legacy. Requires authentication."""
    service = PrescriptionsService(db)
    prescription = await service.get_prescription_by_id(prescription_id)
    if prescription:
        file_url = prescription.file_url
        file_name = prescription.file_name
        file_type = prescription.file_type or "application/octet-stream"
    else:
        entry = get_prescription_from_manifest(settings.LOCAL_STORAGE_PATH, str(prescription_id))
        if not entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Prescription with ID {prescription_id} not found"
            )
        file_url = entry["file_url"]
        file_name = entry["file_name"]
        file_type = entry.get("file_type") or "application/octet-stream"

    if file_url.startswith("/storage/"):
        local_path = Path(settings.LOCAL_STORAGE_PATH) / file_url.replace("/storage/", "", 1)
        if not local_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prescription file not found on disk"
            )
        return FileResponse(
            path=str(local_path),
            filename=file_name,
            media_type=file_type
        )
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
