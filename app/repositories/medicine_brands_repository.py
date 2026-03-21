"""Data access for medicine_brand_offerings (sellable medicine + shared brand)."""

from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base_repository import BaseRepository
from app.db.models import MedicineBrandOffering


class MedicineBrandsRepository(BaseRepository[MedicineBrandOffering]):
    def __init__(self, session: AsyncSession):
        super().__init__(MedicineBrandOffering, session)

    def _get_searchable_fields(self) -> List[str]:
        return ["description"]
