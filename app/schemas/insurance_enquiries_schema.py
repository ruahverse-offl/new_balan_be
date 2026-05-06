"""
Insurance Enquiries Schema
Pydantic models for insurance_enquiries resource
"""

from typing import Optional
from pydantic import Field
from datetime import datetime
from uuid import UUID
from app.schemas.common import ListResponse, BaseCreateRequest, BaseUpdateRequest, BaseResponse


class InsuranceEnquiryCreateRequest(BaseCreateRequest):
    customer_name: str = Field(..., max_length=255)
    customer_phone: str = Field(..., max_length=15)
    customer_age: Optional[int] = Field(None, ge=0, le=150)
    family_size: Optional[int] = Field(None, ge=1, le=20)
    plan_type: Optional[str] = Field(None, max_length=100)
    message: Optional[str] = Field(None)


class InsuranceEnquiryUpdateRequest(BaseUpdateRequest):
    status: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = Field(None)


class InsuranceEnquiryResponse(BaseResponse):
    id: UUID
    customer_name: str
    customer_phone: str
    customer_age: Optional[int] = None
    family_size: Optional[int] = None
    plan_type: Optional[str] = None
    message: Optional[str] = None
    status: str
    notes: Optional[str] = None

    model_config = {"from_attributes": True}


class InsuranceEnquiryListResponse(ListResponse[InsuranceEnquiryResponse]):
    pass
