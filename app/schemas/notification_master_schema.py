"""
Notification Master Schema
Pydantic models for notification template definitions.

Design notes:
- One master row per event code (e.g., ORDER_PLACED, ORDER_DELIVERED).
- Each row can hold multiple channel templates.
- Each channel template stores its own message variables.
"""

from typing import Dict, List, Literal, Optional
from uuid import UUID

from pydantic import Field

from app.schemas.common import BaseCreateRequest, BaseResponse, BaseUpdateRequest, ListResponse

NotificationChannelCode = Literal["push", "sms", "email", "whatsapp"]


class NotificationChannelTemplate(BaseCreateRequest):
    """Template payload for one channel."""

    title_template: Optional[str] = Field(
        None,
        description="Channel title template (used mainly for push/email subject style channels)",
    )
    body_template: str = Field(..., description="Body template with variables, e.g. 'Order {{order_reference}} confirmed'")
    message_variables: List[str] = Field(
        default_factory=list,
        description="Allowed variable keys used by this channel template",
    )
    is_enabled: bool = Field(True, description="Whether this channel template is active")


class NotificationMasterCreateRequest(BaseCreateRequest):
    """Create request for notification master template."""

    event_code: str = Field(..., max_length=100, description="Unique event code like ORDER_PLACED")
    event_name: str = Field(..., max_length=255, description="Human-friendly event name")
    description: Optional[str] = Field(None, description="Optional event/template notes")
    channel_templates: Dict[NotificationChannelCode, NotificationChannelTemplate] = Field(
        default_factory=dict,
        description="Per-channel templates and variable definitions",
    )
    is_active: bool = Field(True, description="Whether this template is active")

    model_config = {
        "json_schema_extra": {
            "example": {
                "event_code": "ORDER_PLACED",
                "event_name": "Order placed by customer",
                "description": "Sent immediately after successful payment",
                "channel_templates": {
                    "push": {
                        "title_template": "Order {{order_reference}} placed",
                        "body_template": "Hi {{customer_name}}, your order total is ₹{{final_amount}}.",
                        "message_variables": ["order_reference", "customer_name", "final_amount"],
                        "is_enabled": True,
                    },
                    "email": {
                        "title_template": "Your order {{order_reference}} is confirmed",
                        "body_template": "Dear {{customer_name}}, we received your order.",
                        "message_variables": ["order_reference", "customer_name"],
                        "is_enabled": True,
                    },
                },
                "is_active": True,
            }
        }
    }


class NotificationMasterUpdateRequest(BaseUpdateRequest):
    """Partial update request for notification master template."""

    event_name: Optional[str] = Field(None, max_length=255, description="Event display name")
    description: Optional[str] = Field(None, description="Optional event/template notes")
    channel_templates: Optional[Dict[NotificationChannelCode, NotificationChannelTemplate]] = Field(
        None,
        description="Replace full channel template map",
    )
    is_active: Optional[bool] = Field(None, description="Whether template is active")


class NotificationMasterResponse(BaseResponse):
    """Response model for notification master template."""

    id: UUID = Field(..., description="Notification master ID")
    event_code: str = Field(..., description="Unique event code")
    event_name: str = Field(..., description="Event display name")
    description: Optional[str] = Field(None, description="Template notes")
    channel_templates: Dict[NotificationChannelCode, NotificationChannelTemplate] = Field(
        default_factory=dict,
        description="Per-channel templates and variables",
    )
    is_active: bool = Field(..., description="Whether template is active")


class NotificationMasterListResponse(ListResponse[NotificationMasterResponse]):
    """Response model for notification master list with pagination."""

    pass

