"""Pydantic models for medicine_categories resource."""

from typing import Optional
from pydantic import Field
from uuid import UUID
from app.schemas.common import ListResponse, BaseCreateRequest, BaseUpdateRequest, BaseResponse


class MedicineCategoryCreateRequest(BaseCreateRequest):
    name: str = Field(..., max_length=255, description="Medicine category name")
    description: Optional[str] = Field(None, description="Description")

    model_config = {"json_schema_extra": {"example": {"name": "Analgesics", "description": "Pain relief"}}}


class MedicineCategoryUpdateRequest(BaseUpdateRequest):
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class MedicineCategoryResponse(BaseResponse):
    id: UUID = Field(...)
    name: str = Field(...)
    description: Optional[str] = None
    is_active: bool = Field(...)


class MedicineCategoryListResponse(ListResponse[MedicineCategoryResponse]):
    pass
