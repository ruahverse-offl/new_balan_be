"""
KPI routes — single summary endpoint replacing legacy dashboard APIs.
"""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_connection import get_db
from app.schemas.kpi_summary_schema import KpiSummaryResponse
from app.services.kpi_summary_service import KpiSummaryService
from app.utils.rbac import require_permission

router = APIRouter(prefix="/api/v1/kpi", tags=["kpi"])


@router.get("/summary", response_model=KpiSummaryResponse)
async def get_kpi_summary(
    _: UUID = Depends(require_permission("DASHBOARD_VIEW")),
    db: AsyncSession = Depends(get_db),
) -> KpiSummaryResponse:
    """
    Return aggregate KPIs: total orders, total medicines, total sales (sum of order final_amount).

    Requires DASHBOARD_VIEW permission.
    """
    service = KpiSummaryService(db)
    return await service.get_summary()
