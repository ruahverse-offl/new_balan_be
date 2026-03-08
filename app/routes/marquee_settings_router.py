"""
Marquee Settings Router
Dedicated API for coupon marquee visibility only. Does not touch delivery settings.
Reads/writes only the show_marquee field on the delivery_settings singleton.
"""

import logging
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_connection import get_db
from app.repositories.delivery_settings_repository import DeliverySettingsRepository
from app.schemas.marquee_settings_schema import MarqueeSettingsResponse, MarqueeSettingsUpdate
from app.utils.auth import get_current_user_id_optional
from app.utils.request_utils import get_client_ip

router = APIRouter(prefix="/api/v1/marquee-settings", tags=["marquee-settings"])
logger = logging.getLogger(__name__)


@router.get("/", response_model=MarqueeSettingsResponse)
async def get_marquee_settings(db: AsyncSession = Depends(get_db)):
    """Get coupon marquee visibility only. Does not return or touch delivery settings."""
    repo = DeliverySettingsRepository(db)
    settings = await repo.get_singleton()
    if not settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Settings not found. Create delivery settings first."
        )
    return MarqueeSettingsResponse(show_marquee=bool(settings.show_marquee))


@router.patch("/", response_model=MarqueeSettingsResponse)
async def update_marquee_settings(
    data: MarqueeSettingsUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID | None = Depends(get_current_user_id_optional),
):
    """Update only coupon marquee visibility. Delivery settings are not modified."""
    user_id = current_user_id or UUID("00000000-0000-0000-0000-000000000000")
    ip_address = get_client_ip(request)
    repo = DeliverySettingsRepository(db)
    settings = await repo.get_singleton()
    if not settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Settings not found. Create delivery settings first."
        )
    try:
        updated = await repo.update(
            settings.id,
            {"show_marquee": data.show_marquee},
            user_id,
            ip_address,
        )
        if not updated:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Update failed")
        return MarqueeSettingsResponse(show_marquee=bool(updated.show_marquee))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("PATCH marquee-settings failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e) or "Failed to update marquee visibility",
        )
