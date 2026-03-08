"""
Role Permissions Repository
Data access layer for role_permissions
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base_repository import BaseRepository
from app.db.models import RolePermission


class RolePermissionsRepository(BaseRepository[RolePermission]):
    """Repository for role_permissions table."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(RolePermission, session)
    
    def _get_searchable_fields(self) -> List[str]:
        """Get searchable fields for role_permissions."""
        return []  # No text fields to search
