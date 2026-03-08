"""
Insurance Enquiries Repository
Data access layer for insurance_enquiries
"""

from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base_repository import BaseRepository
from app.db.models import InsuranceEnquiry


class InsuranceEnquiriesRepository(BaseRepository[InsuranceEnquiry]):
    """Repository for insurance_enquiries table."""

    def __init__(self, session: AsyncSession):
        super().__init__(InsuranceEnquiry, session)

    def _get_searchable_fields(self) -> List[str]:
        """Get searchable fields for insurance enquiries."""
        return ["customer_name", "customer_phone", "plan_type", "status", "message", "admin_notes"]
