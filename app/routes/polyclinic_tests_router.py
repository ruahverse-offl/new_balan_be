"""
Polyclinic Tests Router
FastAPI routes for polyclinic_tests resource
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_connection import get_db
from app.services.polyclinic_tests_service import PolyclinicTestsService
from app.schemas.polyclinic_tests_schema import (
    PolyclinicTestCreateRequest,
    PolyclinicTestUpdateRequest,
    PolyclinicTestResponse,
    PolyclinicTestListResponse
)
from app.utils.rbac import require_permission
from app.utils.request_utils import get_client_ip

router = APIRouter(prefix="/api/v1/polyclinic-tests", tags=["polyclinic-tests"])


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=PolyclinicTestResponse)
async def create_polyclinic_test(
    data: PolyclinicTestCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(require_permission("MEDICINE_CREATE"))
):
    """Create a new polyclinic test. Requires MEDICINE_CREATE permission."""
    ip_address = get_client_ip(request)
    service = PolyclinicTestsService(db)
    test = await service.create_polyclinic_test(data, current_user_id, ip_address)
    return test


@router.get("/{test_id}", response_model=PolyclinicTestResponse)
async def get_polyclinic_test_by_id(
    test_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get polyclinic test by ID."""
    service = PolyclinicTestsService(db)
    test = await service.get_polyclinic_test_by_id(test_id)
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Polyclinic test with ID {test_id} not found"
        )
    return test


@router.get("/", response_model=PolyclinicTestListResponse)
async def get_polyclinic_tests_list(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    search: Optional[str] = Query(default=None),
    sort_by: Optional[str] = Query(default="created_at"),
    sort_order: Optional[str] = Query(default="desc", pattern="^(asc|desc)$"),
    is_active: Optional[bool] = Query(default=None),
    db: AsyncSession = Depends(get_db)
):
    """Get list of polyclinic tests with pagination, search, and sort."""
    service = PolyclinicTestsService(db)
    result = await service.get_polyclinic_tests_list(
        limit=limit, offset=offset, search=search, sort_by=sort_by, sort_order=sort_order,
        is_active=is_active
    )
    return result


@router.patch("/{test_id}", response_model=PolyclinicTestResponse)
async def update_polyclinic_test(
    test_id: UUID,
    data: PolyclinicTestUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(require_permission("MEDICINE_UPDATE"))
):
    """Update a polyclinic test. Requires MEDICINE_UPDATE permission."""
    ip_address = get_client_ip(request)
    service = PolyclinicTestsService(db)
    test = await service.update_polyclinic_test(test_id, data, current_user_id, ip_address)
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Polyclinic test with ID {test_id} not found"
        )
    return test


@router.delete("/{test_id}", status_code=status.HTTP_200_OK)
async def delete_polyclinic_test(
    test_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(require_permission("MEDICINE_DELETE"))
):
    """Soft delete a polyclinic test. Requires MEDICINE_DELETE permission."""
    ip_address = get_client_ip(request)
    service = PolyclinicTestsService(db)
    deleted = await service.delete_polyclinic_test(test_id, current_user_id, ip_address)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Polyclinic test with ID {test_id} not found"
        )
    return {"message": "Polyclinic test deleted successfully", "id": str(test_id)}
