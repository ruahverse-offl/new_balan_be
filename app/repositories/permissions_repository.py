"""
Permissions Repository
Data access layer for permissions
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base_repository import BaseRepository
from app.db.models import Permission


class PermissionsRepository(BaseRepository[Permission]):
    """Repository for permissions table."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Permission, session)
    
    def _get_searchable_fields(self) -> List[str]:
        """Get searchable fields for permissions."""
        return ["code", "description"]
