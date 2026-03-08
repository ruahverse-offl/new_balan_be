"""
Polyclinic Tests Service
Business logic layer for polyclinic_tests
"""

from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.repositories.polyclinic_tests_repository import PolyclinicTestsRepository
from app.schemas.polyclinic_tests_schema import (
    PolyclinicTestCreateRequest,
    PolyclinicTestUpdateRequest,
    PolyclinicTestResponse,
    PolyclinicTestListResponse
)
from app.schemas.common import PaginationResponse
from app.services.base_service import BaseService

logger = logging.getLogger(__name__)


class PolyclinicTestsService(BaseService):
    """Service for polyclinic_tests operations."""
    
    def __init__(self, session: AsyncSession):
        repository = PolyclinicTestsRepository(session)
        super().__init__(repository, session)
    
    async def create_polyclinic_test(
        self,
        data: PolyclinicTestCreateRequest,
        created_by: UUID,
        created_ip: str
    ) -> PolyclinicTestResponse:
        """Create a new polyclinic test."""
        logger.info(f"Creating polyclinic test: {data.name}")
        test_data = data.model_dump()
        test_data["is_active"] = True
        test = await self.repository.create(test_data, created_by, created_ip)
        test_dict = self._model_to_dict(test)
        return PolyclinicTestResponse(**test_dict)
    
    async def get_polyclinic_test_by_id(self, test_id: UUID) -> Optional[PolyclinicTestResponse]:
        """Get polyclinic test by ID."""
        test = await self.repository.get_by_id(test_id)
        if not test:
            return None
        test_dict = self._model_to_dict(test)
        return PolyclinicTestResponse(**test_dict)
    
    async def get_polyclinic_tests_list(
        self,
        limit: int = 20,
        offset: int = 0,
        search: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> PolyclinicTestListResponse:
        """Get list of polyclinic tests with pagination, search, and sort."""
        tests, pagination = await self.repository.get_list(
            limit=limit, offset=offset, search=search, sort_by=sort_by, sort_order=sort_order,
            additional_filters={"is_active": is_active} if is_active is not None else None
        )
        test_responses = [
            PolyclinicTestResponse(**self._model_to_dict(t)) for t in tests
        ]
        return PolyclinicTestListResponse(
            items=test_responses,
            pagination=PaginationResponse(**pagination)
        )
    
    async def update_polyclinic_test(
        self,
        test_id: UUID,
        data: PolyclinicTestUpdateRequest,
        updated_by: UUID,
        updated_ip: str
    ) -> Optional[PolyclinicTestResponse]:
        """Update a polyclinic test."""
        logger.info(f"Updating polyclinic test: {test_id}")
        test_data = data.model_dump(exclude_unset=True)
        test = await self.repository.update(test_id, test_data, updated_by, updated_ip)
        if not test:
            return None
        test_dict = self._model_to_dict(test)
        return PolyclinicTestResponse(**test_dict)
    
    async def delete_polyclinic_test(
        self,
        test_id: UUID,
        updated_by: UUID,
        updated_ip: str
    ) -> bool:
        """Soft delete a polyclinic test."""
        logger.info(f"Deleting polyclinic test: {test_id}")
        return await self.repository.soft_delete(test_id, updated_by, updated_ip)
