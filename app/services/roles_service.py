"""
Roles Service
Business logic layer for roles
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.repositories.roles_repository import RolesRepository
from app.schemas.roles_schema import (
    RoleCreateRequest,
    RoleUpdateRequest,
    RoleResponse,
    RoleListResponse
)
from app.schemas.common import PaginationResponse
from app.services.base_service import BaseService

logger = logging.getLogger(__name__)


class RolesService(BaseService):
    """Service for roles operations."""
    
    def __init__(self, session: AsyncSession):
        repository = RolesRepository(session)
        super().__init__(repository, session)
    
    async def create_role(
        self,
        data: RoleCreateRequest,
        created_by: UUID,
        created_ip: str
    ) -> RoleResponse:
        """
        Create a new role.
        
        Args:
            data: Role creation data
            created_by: User ID who created the role
            created_ip: IP address of creator
            
        Returns:
            Created role response
        """
        logger.info(f"Creating role: {data.name}")
        
        # Convert request to dict
        role_data = data.model_dump()
        
        # Automatically set is_active to True
        role_data["is_active"] = True
        
        # Create in repository
        role = await self.repository.create(role_data, created_by, created_ip)
        
        # Convert to response
        role_dict = self._model_to_dict(role)
        return RoleResponse(**role_dict)
    
    async def get_role_by_id(self, role_id: UUID) -> Optional[RoleResponse]:
        """
        Get role by ID.
        
        Args:
            role_id: Role ID
            
        Returns:
            Role response or None if not found
        """
        role = await self.repository.get_by_id(role_id)
        if not role:
            return None
        
        role_dict = self._model_to_dict(role)
        return RoleResponse(**role_dict)
    
    async def get_roles_list(
        self,
        limit: int = 20,
        offset: int = 0,
        search: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None
    ) -> RoleListResponse:
        """
        Get list of roles with pagination, search, and sort.
        
        Args:
            limit: Number of records per page
            offset: Number of records to skip
            search: Search term
            sort_by: Field name to sort by
            sort_order: Sort order ('asc' or 'desc')
            
        Returns:
            Role list response with pagination
        """
        # Get from repository
        roles, pagination = await self.repository.get_list(
            limit=limit,
            offset=offset,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        # Convert to response models
        role_responses = [
            RoleResponse(**self._model_to_dict(role))
            for role in roles
        ]
        
        return RoleListResponse(
            items=role_responses,
            pagination=PaginationResponse(**pagination)
        )
    
    async def update_role(
        self,
        role_id: UUID,
        data: RoleUpdateRequest,
        updated_by: UUID,
        updated_ip: str
    ) -> Optional[RoleResponse]:
        """
        Update a role.
        
        Args:
            role_id: Role ID
            data: Role update data
            updated_by: User ID who updated the role
            updated_ip: IP address of updater
            
        Returns:
            Updated role response or None if not found
        """
        logger.info(f"Updating role: {role_id}")
        
        # Convert request to dict (exclude None values)
        update_data = {k: v for k, v in data.model_dump().items() if v is not None}
        
        # Update in repository
        role = await self.repository.update(role_id, update_data, updated_by, updated_ip)
        if not role:
            return None
        
        # Convert to response
        role_dict = self._model_to_dict(role)
        return RoleResponse(**role_dict)
    
    async def delete_role(
        self,
        role_id: UUID,
        updated_by: UUID,
        updated_ip: str
    ) -> bool:
        """
        Soft delete a role.
        
        Args:
            role_id: Role ID
            updated_by: User ID who deleted the role
            updated_ip: IP address of deleter
            
        Returns:
            True if deleted, False if not found
        """
        logger.info(f"Deleting role: {role_id}")
        return await self.repository.soft_delete(role_id, updated_by, updated_ip)
