"""
Pharmacist Profiles Service
Business logic layer for pharmacist_profiles
"""

from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.repositories.pharmacist_profiles_repository import PharmacistProfilesRepository
from app.schemas.pharmacist_profiles_schema import (
    PharmacistProfileCreateRequest,
    PharmacistProfileUpdateRequest,
    PharmacistProfileResponse,
    PharmacistProfileListResponse
)
from app.schemas.common import PaginationResponse
from app.services.base_service import BaseService

logger = logging.getLogger(__name__)


class PharmacistProfilesService(BaseService):
    """Service for pharmacist_profiles operations."""
    
    def __init__(self, session: AsyncSession):
        repository = PharmacistProfilesRepository(session)
        super().__init__(repository, session)
    
    async def create_pharmacist_profile(
        self,
        data: PharmacistProfileCreateRequest,
        created_by: UUID,
        created_ip: str
    ) -> PharmacistProfileResponse:
        """Create a new pharmacist profile."""
        logger.info(f"Creating pharmacist profile: {data.user_id}")
        profile_data = data.model_dump()
        # Automatically set is_active to True
        profile_data["is_active"] = True
        profile = await self.repository.create(profile_data, created_by, created_ip)
        profile_dict = self._model_to_dict(profile)
        return PharmacistProfileResponse(**profile_dict)
    
    async def get_pharmacist_profile_by_id(self, user_id: UUID) -> Optional[PharmacistProfileResponse]:
        """Get pharmacist profile by user ID."""
        # Note: pharmacist_profiles uses user_id as primary key
        profile = await self.repository.get_by_id(user_id)
        if not profile:
            return None
        profile_dict = self._model_to_dict(profile)
        return PharmacistProfileResponse(**profile_dict)
    
    async def get_pharmacist_profiles_list(
        self,
        limit: int = 20,
        offset: int = 0,
        search: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None
    ) -> PharmacistProfileListResponse:
        """Get list of pharmacist profiles with pagination, search, and sort."""
        profiles, pagination = await self.repository.get_list(
            limit=limit, offset=offset, search=search, sort_by=sort_by, sort_order=sort_order
        )
        profile_responses = [
            PharmacistProfileResponse(**self._model_to_dict(p)) for p in profiles
        ]
        return PharmacistProfileListResponse(
            items=profile_responses,
            pagination=PaginationResponse(**pagination)
        )
    
    async def update_pharmacist_profile(
        self,
        user_id: UUID,
        data: PharmacistProfileUpdateRequest,
        updated_by: UUID,
        updated_ip: str
    ) -> Optional[PharmacistProfileResponse]:
        """Update a pharmacist profile."""
        logger.info(f"Updating pharmacist profile: {user_id}")
        update_data = {k: v for k, v in data.model_dump().items() if v is not None}
        profile = await self.repository.update(user_id, update_data, updated_by, updated_ip)
        if not profile:
            return None
        profile_dict = self._model_to_dict(profile)
        return PharmacistProfileResponse(**profile_dict)
    
    async def delete_pharmacist_profile(
        self,
        user_id: UUID,
        updated_by: UUID,
        updated_ip: str
    ) -> bool:
        """Soft delete a pharmacist profile."""
        logger.info(f"Deleting pharmacist profile: {user_id}")
        return await self.repository.soft_delete(user_id, updated_by, updated_ip)
