"""
Permissions Service
Business logic layer for permissions
"""

from typing import Optional
from uuid import UUID
from sqlalchemy import update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.db.models import RolePermission
from app.repositories.permissions_repository import PermissionsRepository
from app.schemas.permissions_schema import (
    PermissionCreateRequest,
    PermissionUpdateRequest,
    PermissionResponse,
    PermissionListResponse
)
from app.schemas.common import PaginationResponse
from app.services.base_service import BaseService
from app.utils.datetime_utils import get_current_ist_time

logger = logging.getLogger(__name__)


class PermissionsService(BaseService):
    """Service for permissions operations."""
    
    def __init__(self, session: AsyncSession):
        repository = PermissionsRepository(session)
        super().__init__(repository, session)
    
    async def create_permission(
        self,
        data: PermissionCreateRequest,
        created_by: UUID,
        created_ip: str
    ) -> PermissionResponse:
        """Create a new permission."""
        logger.info(f"Creating permission: {data.code}")
        permission_data = data.model_dump()
        # Automatically set is_active to True
        permission_data["is_active"] = True
        permission = await self.repository.create(permission_data, created_by, created_ip)
        permission_dict = self._model_to_dict(permission)
        return PermissionResponse(**permission_dict)
    
    async def get_permission_by_id(self, permission_id: UUID) -> Optional[PermissionResponse]:
        """Get permission by ID."""
        permission = await self.repository.get_by_id(permission_id)
        if not permission:
            return None
        permission_dict = self._model_to_dict(permission)
        return PermissionResponse(**permission_dict)
    
    async def get_permissions_list(
        self,
        limit: int = 20,
        offset: int = 0,
        search: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None
    ) -> PermissionListResponse:
        """Get list of permissions with pagination, search, and sort."""
        permissions, pagination = await self.repository.get_list(
            limit=limit, offset=offset, search=search, sort_by=sort_by, sort_order=sort_order
        )
        permission_responses = [
            PermissionResponse(**self._model_to_dict(p)) for p in permissions
        ]
        return PermissionListResponse(
            items=permission_responses,
            pagination=PaginationResponse(**pagination)
        )
    
    async def update_permission(
        self,
        permission_id: UUID,
        data: PermissionUpdateRequest,
        updated_by: UUID,
        updated_ip: str
    ) -> Optional[PermissionResponse]:
        """Update a permission."""
        logger.info(f"Updating permission: {permission_id}")
        update_data = {k: v for k, v in data.model_dump().items() if v is not None}
        permission = await self.repository.update(permission_id, update_data, updated_by, updated_ip)
        if not permission:
            return None
        permission_dict = self._model_to_dict(permission)
        return PermissionResponse(**permission_dict)
    
    async def delete_permission(
        self,
        permission_id: UUID,
        updated_by: UUID,
        updated_ip: str
    ) -> bool:
        """
        Soft delete a permission and all role↔permission links for it.

        RBAC already ignores deleted permissions, but removing links keeps the
        assign-permissions UI and reports consistent.
        """
        logger.info(f"Deleting permission: {permission_id}")
        perm = await self.repository.get_by_id(permission_id)
        if not perm or getattr(perm, "is_deleted", False):
            return False

        now = get_current_ist_time()
        await self.session.execute(
            sa_update(RolePermission)
            .where(RolePermission.permission_id == permission_id)
            .where(RolePermission.is_deleted == False)
            .values(
                is_deleted=True,
                updated_by=updated_by,
                updated_ip=updated_ip,
                updated_at=now,
            )
        )
        await self.session.flush()
        return await self.repository.soft_delete(permission_id, updated_by, updated_ip)
