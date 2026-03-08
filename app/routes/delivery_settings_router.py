"""
Delivery Settings Router
FastAPI routes for delivery_settings resource
"""

import logging
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_connection import get_db
from app.services.delivery_settings_service import DeliverySettingsService
from app.schemas.delivery_settings_schema import (
    DeliverySettingCreateRequest,
    DeliverySettingUpdateRequest,
    DeliverySettingResponse
)
from app.utils.auth import get_current_user_id_optional
from app.utils.request_utils import get_client_ip

router = APIRouter(prefix="/api/v1/delivery-settings", tags=["delivery-settings"])


@router.get("/")
async def get_delivery_settings(
    db: AsyncSession = Depends(get_db)
):
    """Get delivery settings (singleton)."""
    service = DeliverySettingsService(db)
    settings = await service.get_delivery_settings()
    if not settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery settings not found"
        )
    return JSONResponse(content=settings)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_delivery_settings(
    data: DeliverySettingCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: Optional[UUID] = Depends(get_current_user_id_optional)
):
    """Create delivery settings (singleton)."""
    user_id = current_user_id or UUID("00000000-0000-0000-0000-000000000000")
    ip_address = get_client_ip(request)
    service = DeliverySettingsService(db)
    settings = await service.create_or_update_delivery_settings(data, user_id, ip_address)
    return JSONResponse(status_code=201, content=settings)


@router.patch("/")
async def update_delivery_settings(
    data: DeliverySettingUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: Optional[UUID] = Depends(get_current_user_id_optional)
):
    """Update delivery settings (singleton)."""
    try:
        user_id = current_user_id or UUID("00000000-0000-0000-0000-000000000000")
        ip_address = get_client_ip(request)
        service = DeliverySettingsService(db)
        settings = await service.create_or_update_delivery_settings(
            data, user_id, ip_address, updated_by=user_id, updated_ip=ip_address
        )
        return JSONResponse(content=settings)
    except HTTPException:
        raise
    except Exception as e:
        logging.getLogger(__name__).exception("PATCH delivery-settings failed")
        err_msg = f"{type(e).__name__}: {str(e)}"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=err_msg or "Failed to update delivery settings",
        )
