"""
KPI summary service
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.kpi_summary_repository import KpiSummaryRepository
from app.schemas.kpi_summary_schema import KpiSummaryResponse


class KpiSummaryService:
    """Service for loading global KPI aggregates."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_summary(self) -> KpiSummaryResponse:
        """
        Load total orders, total medicines, and total sales (sum of order final_amount).

        Returns:
            KpiSummaryResponse with the three KPI fields.
        """
        repo = KpiSummaryRepository(self._session)
        data = await repo.get_summary()
        return KpiSummaryResponse(**data)
