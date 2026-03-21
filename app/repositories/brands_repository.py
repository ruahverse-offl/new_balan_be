"""Data access for brands."""

from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base_repository import BaseRepository
from app.db.models import Brand


class BrandsRepository(BaseRepository[Brand]):
    def __init__(self, session: AsyncSession):
        super().__init__(Brand, session)

    def _get_searchable_fields(self) -> List[str]:
        return ["name", "description"]
