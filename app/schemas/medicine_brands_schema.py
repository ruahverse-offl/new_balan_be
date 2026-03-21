"""
Schemas for medicine–brand offerings (junction).
API path remains /medicine-brands for compatibility; each row links medicine_id + brand_id.
"""

from typing import Optional
from pydantic import Field
from uuid import UUID
from decimal import Decimal
from app.schemas.common import ListResponse, BaseCreateRequest, BaseUpdateRequest, BaseResponse


class MedicineBrandCreateRequest(BaseCreateRequest):
    medicine_id: UUID = Field(..., description="Medicine ID")
    brand_id: UUID = Field(..., description="Shared brand ID")
    manufacturer: str = Field(..., max_length=255)
    mrp: Decimal = Field(...)
    description: Optional[str] = None
    is_available: Optional[bool] = Field(True)

    model_config = {"json_schema_extra": {"example": {
        "medicine_id": "m1e123-4567-8901-2345-678901234567",
        "brand_id": "b1e123-4567-8901-2345-678901234567",
        "manufacturer": "GSK",
        "mrp": 25.00,
        "description": "500mg strip",
    }}}


class MedicineBrandUpdateRequest(BaseUpdateRequest):
    medicine_id: Optional[UUID] = None
    brand_id: Optional[UUID] = None
    manufacturer: Optional[str] = Field(None, max_length=255)
    mrp: Optional[Decimal] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    is_available: Optional[bool] = None


class MedicineBrandResponse(BaseResponse):
    id: UUID = Field(..., description="Offering ID (use as medicine_brand_id on orders)")
    medicine_id: UUID
    brand_id: UUID
    brand_name: str = Field(..., description="Resolved from brands master")
    manufacturer: str
    mrp: Decimal
    description: Optional[str] = None
    is_active: bool
    is_available: bool

    model_config = {"json_schema_extra": {"example": {
        "id": "mb1e123-4567-8901-2345-678901234567",
        "medicine_id": "m1e123-4567-8901-2345-678901234567",
        "brand_id": "b1e123-4567-8901-2345-678901234567",
        "brand_name": "Crocin",
        "manufacturer": "GSK",
        "mrp": 25.00,
        "is_active": True,
        "is_available": True,
    }}}


class MedicineBrandListResponse(ListResponse[MedicineBrandResponse]):
    pass
