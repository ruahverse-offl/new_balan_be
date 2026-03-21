"""Pydantic models for shared brands master."""

from typing import Optional
from pydantic import Field
from uuid import UUID
from app.schemas.common import ListResponse, BaseCreateRequest, BaseUpdateRequest, BaseResponse


class BrandCreateRequest(BaseCreateRequest):
    name: str = Field(..., max_length=255, description="Brand name (unique)")
    description: Optional[str] = Field(None)


class BrandUpdateRequest(BaseUpdateRequest):
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class BrandResponse(BaseResponse):
    id: UUID
    name: str
    description: Optional[str] = None
    is_active: bool


class BrandListResponse(ListResponse[BrandResponse]):
    pass
