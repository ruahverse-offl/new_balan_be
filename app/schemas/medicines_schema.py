"""Pydantic models for medicines resource."""

from typing import Optional, List
from pydantic import BaseModel, Field, field_serializer
from uuid import UUID
from decimal import Decimal
from app.schemas.common import ListResponse, BaseCreateRequest, BaseUpdateRequest, BaseResponse


class MedicineBrandSummary(BaseModel):
    """Nested offering summary on medicine responses."""

    id: UUID = Field(..., description="Offering ID (cart/order medicine_brand_id)")
    medicine_id: UUID
    brand_id: UUID
    brand_name: str = Field(..., description="From brands master")
    manufacturer: str
    mrp: Decimal
    description: Optional[str] = None
    is_active: bool = True
    is_available: bool = True
    stock_quantity: int = Field(
        default=0,
        ge=0,
        description="On-hand units for this medicine+brand (M_inventory)",
    )

    @field_serializer("mrp")
    def ser_mrp(self, v: Decimal) -> float:
        return float(v) if v is not None else 0.0


class MedicineCreateRequest(BaseCreateRequest):
    name: str = Field(..., max_length=255)
    medicine_category_id: UUID = Field(..., description="Medicine category ID")
    is_prescription_required: bool = Field(False)
    description: Optional[str] = None
    is_available: bool = Field(True)
    image_path: Optional[str] = Field(
        None,
        max_length=512,
        description="Storage path from POST /upload (category=medicine), e.g. medicine/filename.jpg",
    )

    model_config = {"json_schema_extra": {"example": {
        "name": "Paracetamol 500mg",
        "medicine_category_id": "mc1e123-4567-8901-2345-678901234567",
        "is_prescription_required": False,
        "description": "Analgesic",
        "is_available": True,
    }}}


class MedicineUpdateRequest(BaseUpdateRequest):
    name: Optional[str] = Field(None, max_length=255)
    medicine_category_id: Optional[UUID] = None
    is_prescription_required: Optional[bool] = None
    description: Optional[str] = None
    is_available: Optional[bool] = None
    is_active: Optional[bool] = None
    image_path: Optional[str] = Field(
        None,
        max_length=512,
        description="Set to new path or null to remove image",
    )


class MedicineResponse(BaseResponse):
    id: UUID
    name: str
    medicine_category_id: UUID
    medicine_category_name: Optional[str] = Field(None, description="Category name in list/detail")
    is_prescription_required: bool
    description: Optional[str] = None
    is_available: bool
    image_path: Optional[str] = Field(None, description="Relative storage path for product image")
    brands: Optional[List[MedicineBrandSummary]] = Field(None, description="Offerings when include_brands=true")

    model_config = {"json_schema_extra": {"example": {
        "id": "m1e123-4567-8901-2345-678901234567",
        "name": "Paracetamol 500mg",
        "medicine_category_id": "mc1e123-4567-8901-2345-678901234567",
        "is_prescription_required": False,
        "is_available": True,
    }}}


class MedicineListResponse(ListResponse[MedicineResponse]):
    pass
