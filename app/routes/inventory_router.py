"""
Inventory: stock levels, low-stock alerts (INV_STOCK_THRESHOLD).
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.db_connection import get_db
from app.schemas.inventory_schema import (
    InventoryAlertListResponse,
    InventoryStockUpdateRequest,
    StockByOfferingItem,
    StockByOfferingResponse,
)
from app.services import inventory_service
from app.utils.auth import get_current_user_id
from app.utils.rbac import require_permission
from app.utils.request_utils import get_client_ip

router = APIRouter(prefix="/api/v1/inventory", tags=["inventory"])


@router.get("/stock", response_model=StockByOfferingResponse)
async def get_stock_by_offerings(
    offering_ids: str = Query(
        ...,
        description="Comma-separated medicine_brand_offering UUIDs",
    ),
    db: AsyncSession = Depends(get_db),
):
    """Return current stock for one or more offerings (storefront / cart)."""
    raw = [x.strip() for x in offering_ids.split(",") if x.strip()]
    if not raw:
        return StockByOfferingResponse(items=[])
    ids: list[UUID] = []
    for s in raw:
        try:
            ids.append(UUID(s))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid UUID in offering_ids: {s}",
            )
    stocks = await inventory_service.get_stock_map(db, ids)
    items = [StockByOfferingItem(medicine_brand_offering_id=oid, stock_quantity=stocks.get(oid, 0)) for oid in ids]
    return StockByOfferingResponse(items=items)


@router.get("/alerts", response_model=InventoryAlertListResponse)
async def list_inventory_alerts(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    _current_user_id: UUID = Depends(require_permission("INVENTORY_VIEW")),
):
    """Active low-stock alerts (medicine under brand below threshold)."""
    items = await inventory_service.list_alerts_with_labels(db, limit=limit, offset=offset)
    return InventoryAlertListResponse(
        items=items,
        threshold=get_settings().INV_STOCK_THRESHOLD,
    )


@router.patch("/offering/{offering_id}")
async def update_offering_stock(
    offering_id: UUID,
    data: InventoryStockUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: UUID = Depends(require_permission("INVENTORY_UPDATE")),
):
    """Set absolute stock for a medicine–brand offering (refill / correction). Removes alert when above threshold."""
    ip = get_client_ip(request)
    try:
        await inventory_service.set_stock_quantity(
            db,
            offering_id,
            data.stock_quantity,
            current_user_id,
            ip,
        )
        await db.commit()
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return {"success": True, "medicine_brand_offering_id": str(offering_id), "stock_quantity": data.stock_quantity}
