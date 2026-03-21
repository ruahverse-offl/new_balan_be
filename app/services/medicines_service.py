"""
Medicines Service
Business logic layer for medicines
"""

from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from sqlalchemy import select, update

from app.repositories.medicines_repository import MedicinesRepository
from app.db.models import MedicineBrandOffering, Brand, MedicineCategory
from app.services import inventory_service
from app.schemas.medicines_schema import (
    MedicineBrandSummary,
    MedicineCreateRequest,
    MedicineUpdateRequest,
    MedicineResponse,
    MedicineListResponse,
)
from app.schemas.common import PaginationResponse
from app.services.base_service import BaseService

logger = logging.getLogger(__name__)


async def _get_medicine_category_name(session, category_id) -> str:
    """Look up medicine category name by ID."""
    if not category_id:
        return "—"
    stmt = select(MedicineCategory.name).where(MedicineCategory.id == category_id)
    result = await session.execute(stmt)
    row = result.first()
    return (row[0] if row else None) or "—"


class MedicinesService(BaseService):
    """Service for medicines operations."""

    def __init__(self, session: AsyncSession):
        repository = MedicinesRepository(session)
        super().__init__(repository, session)

    def _to_brand_summary(
        self, offering: MedicineBrandOffering, brand_name: str, stock_quantity: int = 0
    ) -> MedicineBrandSummary:
        """Map offering row + brand name to nested summary."""
        return MedicineBrandSummary(
            id=offering.id,
            medicine_id=offering.medicine_id,
            brand_id=offering.brand_id,
            brand_name=brand_name,
            manufacturer=offering.manufacturer,
            mrp=offering.mrp,
            description=offering.description,
            is_active=offering.is_active,
            is_available=getattr(offering, "is_available", True),
            stock_quantity=stock_quantity,
        )

    async def _fetch_offerings_grouped_by_medicine_id(
        self, medicine_ids: list[UUID]
    ) -> dict[UUID, list[tuple[MedicineBrandOffering, str]]]:
        """Load non-deleted offerings for the given medicine IDs with brand names."""
        if not medicine_ids:
            return {}
        stmt = (
            select(MedicineBrandOffering, Brand.name)
            .join(Brand, MedicineBrandOffering.brand_id == Brand.id)
            .where(MedicineBrandOffering.medicine_id.in_(medicine_ids))
            .where(MedicineBrandOffering.is_deleted == False)  # noqa: E712
            .order_by(Brand.name)
        )
        result = await self.session.execute(stmt)
        grouped: dict[UUID, list[tuple[MedicineBrandOffering, str]]] = {}
        for offering, bname in result:
            grouped.setdefault(offering.medicine_id, []).append((offering, bname or ""))
        return grouped

    async def create_medicine(
        self,
        data: MedicineCreateRequest,
        created_by: UUID,
        created_ip: str,
    ) -> MedicineResponse:
        """Create a new medicine."""
        logger.info(
            "Creating medicine: %s with medicine_category_id=%s",
            data.name,
            data.medicine_category_id,
        )
        medicine_data = data.model_dump()
        medicine_data["is_active"] = True
        medicine_data.setdefault("is_available", True)
        medicine = await self.repository.create(medicine_data, created_by, created_ip)
        medicine_dict = self._model_to_dict(medicine)
        medicine_dict["medicine_category_name"] = await _get_medicine_category_name(
            self.session, medicine.medicine_category_id
        )
        return MedicineResponse(**medicine_dict)

    async def get_medicine_by_id(
        self, medicine_id: UUID, *, include_brands: bool = False
    ) -> Optional[MedicineResponse]:
        """Get medicine by ID. Optionally include nested brand offerings."""
        medicine = await self.repository.get_by_id(medicine_id)
        if not medicine:
            return None
        medicine_dict = self._model_to_dict(medicine)
        medicine_dict["medicine_category_name"] = await _get_medicine_category_name(
            self.session, medicine.medicine_category_id
        )
        if include_brands:
            grouped = await self._fetch_offerings_grouped_by_medicine_id([medicine_id])
            pairs = grouped.get(medicine_id, [])
            oids = [o.id for o, _ in pairs]
            stock_map = await inventory_service.get_stock_map(self.session, oids)
            medicine_dict["brands"] = [
                self._to_brand_summary(o, bn, stock_map.get(o.id, 0)) for o, bn in pairs
            ]
        return MedicineResponse(**medicine_dict)

    async def get_medicines_list(
        self,
        limit: int = 20,
        offset: int = 0,
        search: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
        is_available: Optional[bool] = None,
        include_brands: bool = False,
    ) -> MedicineListResponse:
        """List medicines with pagination. Filter by is_available for storefront."""
        additional = {"is_available": is_available} if is_available is not None else None
        medicines, pagination = await self.repository.get_list(
            limit=limit,
            offset=offset,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            additional_filters=additional,
        )
        category_ids = [m.medicine_category_id for m in medicines if m.medicine_category_id]
        name_by_category_id: dict[str, str] = {}
        if category_ids:
            stmt = select(MedicineCategory.id, MedicineCategory.name).where(
                MedicineCategory.id.in_(category_ids)
            )
            result = await self.session.execute(stmt)
            for row in result:
                name_by_category_id[str(row.id)] = row.name or "—"
        offerings_by_mid: dict[UUID, list[tuple[MedicineBrandOffering, str]]] = {}
        stock_map: dict[UUID, int] = {}
        if include_brands and medicines:
            offerings_by_mid = await self._fetch_offerings_grouped_by_medicine_id(
                [m.id for m in medicines]
            )
            all_oids: list[UUID] = []
            for _mid, plist in offerings_by_mid.items():
                all_oids.extend([o.id for o, _ in plist])
            stock_map = await inventory_service.get_stock_map(self.session, list(dict.fromkeys(all_oids)))
        medicine_responses = []
        for m in medicines:
            d = self._model_to_dict(m)
            d["medicine_category_name"] = name_by_category_id.get(
                str(m.medicine_category_id), "—"
            )
            if include_brands:
                d["brands"] = [
                    self._to_brand_summary(o, bn, stock_map.get(o.id, 0))
                    for o, bn in offerings_by_mid.get(m.id, [])
                ]
            medicine_responses.append(MedicineResponse(**d))
        return MedicineListResponse(
            items=medicine_responses,
            pagination=PaginationResponse(**pagination),
        )

    async def update_medicine(
        self,
        medicine_id: UUID,
        data: MedicineUpdateRequest,
        updated_by: UUID,
        updated_ip: str,
    ) -> Optional[MedicineResponse]:
        """Update a medicine. When is_available is False, cascade to all offerings."""
        update_data = {k: v for k, v in data.model_dump().items() if v is not None}
        logger.info(
            "Updating medicine: %s medicine_category_id=%s",
            medicine_id,
            update_data.get("medicine_category_id"),
        )
        medicine = await self.repository.update(medicine_id, update_data, updated_by, updated_ip)
        if not medicine:
            return None
        if update_data.get("is_available") is False:
            await self.session.execute(
                update(MedicineBrandOffering)
                .where(MedicineBrandOffering.medicine_id == medicine_id)
                .where(MedicineBrandOffering.is_deleted == False)  # noqa: E712
                .values(is_available=False, updated_by=updated_by, updated_ip=updated_ip)
            )
            logger.info("Cascaded is_available=False to all offerings of medicine %s", medicine_id)
        medicine_dict = self._model_to_dict(medicine)
        medicine_dict["medicine_category_name"] = await _get_medicine_category_name(
            self.session, medicine.medicine_category_id
        )
        return MedicineResponse(**medicine_dict)

    async def delete_medicine(
        self,
        medicine_id: UUID,
        updated_by: UUID,
        updated_ip: str,
    ) -> bool:
        """Soft delete a medicine."""
        logger.info("Deleting medicine: %s", medicine_id)
        return await self.repository.soft_delete(medicine_id, updated_by, updated_ip)
