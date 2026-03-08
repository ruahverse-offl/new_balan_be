"""
Product Categories Schema
Pydantic models for product_categories resource
"""

from typing import Optional
from pydantic import Field
from datetime import datetime
from uuid import UUID
from app.schemas.common import ListResponse, BaseCreateRequest, BaseUpdateRequest, BaseResponse


class ProductCategoryCreateRequest(BaseCreateRequest):
    """Request model for creating a product category."""
    
    name: str = Field(..., max_length=100, description="Category name")
    description: Optional[str] = Field(None, description="Category description")
    
    model_config = {"json_schema_extra": {"example": {
        "name": "OTC",
        "description": "Over-the-counter medicines"
    }}}


class ProductCategoryUpdateRequest(BaseUpdateRequest):
    """Request model for updating a product category."""
    
    name: Optional[str] = Field(None, max_length=100, description="Category name")
    description: Optional[str] = Field(None, description="Category description")
    is_active: Optional[bool] = Field(None, description="Whether the category is active")
    
    model_config = {"json_schema_extra": {"example": {
        "name": "OTC",
        "is_active": True
    }}}


class ProductCategoryResponse(BaseResponse):
    """Response model for product category."""
    
    id: UUID = Field(..., description="Category ID")
    name: str = Field(..., description="Category name")
    description: Optional[str] = Field(None, description="Category description")
    is_active: bool = Field(..., description="Whether the category is active")
    
    model_config = {"json_schema_extra": {"example": {
        "id": "pc1e123-4567-8901-2345-678901234567",
        "name": "OTC",
        "description": "Over-the-counter medicines",
        "is_active": True,
        "created_by": "u123e456-7890-1234-5678-901234567890",
        "created_at": "2026-02-01T10:30:00Z",
        "created_ip": "192.168.1.100",
        "updated_by": None,
        "updated_at": None,
        "updated_ip": None,
        "is_deleted": False
    }}}


class ProductCategoryListResponse(ListResponse[ProductCategoryResponse]):
    """Response model for product category list with pagination."""
    pass
