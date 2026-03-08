"""
Users Repository
Data access layer for users
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base_repository import BaseRepository
from app.db.models import User


class UsersRepository(BaseRepository[User]):
    """Repository for users table."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(User, session)
    
    def _get_searchable_fields(self) -> List[str]:
        """Get searchable fields for users."""
        return ["full_name", "mobile_number", "email"]
