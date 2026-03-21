"""Data access for medicine_categories."""

from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base_repository import BaseRepository
from app.db.models import MedicineCategory


class MedicineCategoriesRepository(BaseRepository[MedicineCategory]):
    def __init__(self, session: AsyncSession):
        super().__init__(MedicineCategory, session)

    def _get_searchable_fields(self) -> List[str]:
        return ["name", "description"]
