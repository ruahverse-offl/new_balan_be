"""
Common Pydantic Schemas
Shared models used across multiple resources
"""

from typing import Generic, TypeVar, List
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from uuid import UUID

T = TypeVar('T')


class BaseCreateRequest(BaseModel):
    """
    Base model for Create requests.
    
    Audit fields (created_by, created_at, created_ip) are automatically
    populated from JWT token and request headers, so they should NOT be
    included in CreateRequest models.
    """
    pass


class BaseUpdateRequest(BaseModel):
    """
    Base model for Update requests.
    
    Audit fields (updated_by, updated_at, updated_ip) are automatically
    populated from JWT token and request headers, so they should NOT be
    included in UpdateRequest models.
    """
    pass


class BaseResponse(BaseModel):
    """
    Base model for Response models.
    
    Includes all audit fields that are populated automatically.
    """
    created_by: UUID = Field(..., description="User who created the record")
    created_at: datetime = Field(..., description="Creation timestamp")
    created_ip: str = Field(..., description="IP address of creator")
    updated_by: UUID | None = Field(None, description="User who last updated the record")
    updated_at: datetime | None = Field(None, description="Last update timestamp")
    updated_ip: str | None = Field(None, description="IP address of updater")
    is_deleted: bool = Field(..., description="Soft delete flag")


class PaginationResponse(BaseModel):
    """Pagination metadata for list responses."""
    
    total: int = Field(..., description="Total number of records")
    limit: int = Field(..., description="Number of records per page")
    offset: int = Field(..., description="Number of records skipped")
    has_next: bool = Field(..., description="Whether there are more records")
    has_previous: bool = Field(..., description="Whether there are previous records")
    
    model_config = {"json_schema_extra": {"example": {
        "total": 150,
        "limit": 20,
        "offset": 0,
        "has_next": True,
        "has_previous": False
    }}}


class ListResponse(BaseModel, Generic[T]):
    """Generic list response with pagination."""
    
    items: List[T] = Field(..., description="List of items")
    pagination: PaginationResponse = Field(..., description="Pagination metadata")

    model_config = {"json_schema_extra": {"example": {
        "items": [],
        "pagination": {
            "total": 0,
            "limit": 20,
            "offset": 0,
            "has_next": False,
            "has_previous": False
        }
    }}}


class ErrorDetail(BaseModel):
    """Error detail structure."""
    
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: dict = Field(default_factory=dict, description="Additional error details")


class ErrorResponse(BaseModel):
    """Standard error response format."""
    
    error: ErrorDetail = Field(..., description="Error information")
    request_id: UUID | None = Field(None, description="Request ID for tracking")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Error timestamp")
    
    model_config = {"json_schema_extra": {"example": {
        "error": {
            "code": "RESOURCE_NOT_FOUND",
            "message": "Resource with ID {id} not found",
            "details": {}
        },
        "request_id": "123e4567-e89b-12d3-a456-426614174000",
        "timestamp": "2026-02-01T10:30:00Z"
    }}}
