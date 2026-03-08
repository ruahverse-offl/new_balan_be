"""
Payments Repository
Data access layer for payments
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base_repository import BaseRepository
from app.db.models import Payment


class PaymentsRepository(BaseRepository[Payment]):
    """Repository for payments table."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Payment, session)
    
    def _get_searchable_fields(self) -> List[str]:
        """Get searchable fields for payments."""
        return ["payment_method", "payment_status"]
