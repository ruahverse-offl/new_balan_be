"""
Medicines Repository
Data access layer for medicines
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base_repository import BaseRepository
from app.db.models import Medicine


class MedicinesRepository(BaseRepository[Medicine]):
    """Repository for medicines table."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Medicine, session)
    
    def _get_searchable_fields(self) -> List[str]:
        """Get searchable fields for medicines."""
        return ["name", "dosage_form", "schedule_type", "description"]
