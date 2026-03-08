"""
Role Permissions Service
Business logic layer for role_permissions
"""

from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.repositories.role_permissions_repository import RolePermissionsRepository
from app.schemas.role_permissions_schema import (
    RolePermissionCreateRequest,
    RolePermissionUpdateRequest,
    RolePermissionResponse,
    RolePermissionListResponse
)
from app.schemas.common import PaginationResponse
from app.services.base_service import BaseService

logger = logging.getLogger(__name__)


class RolePermissionsService(BaseService):
    """Service for role_permissions operations."""
    
    def __init__(self, session: AsyncSession):
        repository = RolePermissionsRepository(session)
        super().__init__(repository, session)
    
    async def create_role_permission(
        self,
        data: RolePermissionCreateRequest,
        created_by: UUID,
        created_ip: str
    ) -> RolePermissionResponse:
        """Create a new role permission."""
        logger.info(f"Creating role permission: {data.role_id} - {data.permission_id}")
        role_permission_data = data.model_dump()
        # Automatically set is_active to True
        role_permission_data["is_active"] = True
        role_permission = await self.repository.create(role_permission_data, created_by, created_ip)
        role_permission_dict = self._model_to_dict(role_permission)
        return RolePermissionResponse(**role_permission_dict)
    
    async def get_role_permission_by_id(self, role_permission_id: UUID) -> Optional[RolePermissionResponse]:
        """Get role permission by ID."""
        role_permission = await self.repository.get_by_id(role_permission_id)
        if not role_permission:
            return None
        role_permission_dict = self._model_to_dict(role_permission)
        return RolePermissionResponse(**role_permission_dict)
    
    async def get_role_permissions_list(
        self,
        limit: int = 20,
        offset: int = 0,
        search: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None
    ) -> RolePermissionListResponse:
        """Get list of role permissions with pagination, search, and sort."""
        role_permissions, pagination = await self.repository.get_list(
            limit=limit, offset=offset, search=search, sort_by=sort_by, sort_order=sort_order
        )
        role_permission_responses = [
            RolePermissionResponse(**self._model_to_dict(rp)) for rp in role_permissions
        ]
        return RolePermissionListResponse(
            items=role_permission_responses,
            pagination=PaginationResponse(**pagination)
        )
    
    async def update_role_permission(
        self,
        role_permission_id: UUID,
        data: RolePermissionUpdateRequest,
        updated_by: UUID,
        updated_ip: str
    ) -> Optional[RolePermissionResponse]:
        """Update a role permission."""
        logger.info(f"Updating role permission: {role_permission_id}")
        update_data = {k: v for k, v in data.model_dump().items() if v is not None}
        role_permission = await self.repository.update(role_permission_id, update_data, updated_by, updated_ip)
        if not role_permission:
            return None
        role_permission_dict = self._model_to_dict(role_permission)
        return RolePermissionResponse(**role_permission_dict)
    
    async def delete_role_permission(
        self,
        role_permission_id: UUID,
        updated_by: UUID,
        updated_ip: str
    ) -> bool:
        """Soft delete a role permission."""
        logger.info(f"Deleting role permission: {role_permission_id}")
        return await self.repository.soft_delete(role_permission_id, updated_by, updated_ip)
