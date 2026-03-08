"""
Pharmacist Profiles Repository
Data access layer for pharmacist_profiles
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base_repository import BaseRepository
from app.db.models import PharmacistProfile


class PharmacistProfilesRepository(BaseRepository[PharmacistProfile]):
    """Repository for pharmacist_profiles table."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(PharmacistProfile, session)
    
    def _get_searchable_fields(self) -> List[str]:
        """Get searchable fields for pharmacist_profiles."""
        return ["license_number"]
