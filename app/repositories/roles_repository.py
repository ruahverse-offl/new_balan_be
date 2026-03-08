"""
Roles Repository
Data access layer for roles
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base_repository import BaseRepository
from app.db.models import Role


class RolesRepository(BaseRepository[Role]):
    """Repository for roles table."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Role, session)
    
    def _get_searchable_fields(self) -> List[str]:
        """Get searchable fields for roles."""
        return ["name", "description"]
