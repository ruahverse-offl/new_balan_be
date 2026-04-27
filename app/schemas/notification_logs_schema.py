"""
Notification Logs Schema
Pydantic models for push send attempts and retry tracking.

Retry policy (as requested):
- max_retry_attempts: 3
- retry_interval_minutes: 5
"""

from datetime import datetime
from typing import Any, Dict, Literal, Optional
from uuid import UUID

from pydantic import Field

from app.schemas.common import BaseCreateRequest, BaseResponse, BaseUpdateRequest, ListResponse

NotificationSendStatus = Literal["queued", "sent", "failed", "retrying", "dropped"]
NotificationChannelCode = Literal["push", "sms", "email", "whatsapp"]


class NotificationLogCreateRequest(BaseCreateRequest):
    """Create request for one notification send log row."""

    user_id: UUID = Field(..., description="Target user ID")
    notification_master_id: UUID = Field(..., description="Master template ID used")
    notification_setting_id: Optional[UUID] = Field(None, description="Settings row used for this send")
    channel: NotificationChannelCode = Field("push", description="Delivery channel")
    expo_push_token: Optional[str] = Field(None, max_length=255, description="Token used for push attempt")
    payload_snapshot: Dict[str, Any] = Field(default_factory=dict, description="Resolved payload sent to provider")
    send_status: NotificationSendStatus = Field("queued", description="Current delivery status")
    provider_response: Optional[Dict[str, Any]] = Field(None, description="Raw provider response payload")
    error_message: Optional[str] = Field(None, description="Error text when send fails")
    retry_count: int = Field(0, ge=0, description="Retries already attempted")
    max_retry_attempts: int = Field(3, ge=0, description="Maximum retries before dropping")
    retry_interval_minutes: int = Field(5, ge=1, description="Delay between retries")
    next_retry_at: Optional[datetime] = Field(None, description="When next retry should happen")
    sent_at: Optional[datetime] = Field(None, description="Timestamp when successfully sent")

    model_config = {
        "json_schema_extra": {
            "example": {
                "user_id": "u123e456-7890-1234-5678-901234567890",
                "notification_master_id": "nm1e1234-5678-9012-3456-789012345678",
                "notification_setting_id": "ns1e1234-5678-9012-3456-789012345678",
                "channel": "push",
                "expo_push_token": "ExponentPushToken[xxxxxxxxxxxxxxxxxxxxxx]",
                "payload_snapshot": {
                    "title": "Order NB-1001 delivered",
                    "body": "Hi Ravi, your order has been delivered.",
                    "data": {"order_id": "o1e12345-6789-0123-4567-890123456789"},
                },
                "send_status": "queued",
                "retry_count": 0,
                "max_retry_attempts": 3,
                "retry_interval_minutes": 5,
            }
        }
    }


class NotificationLogUpdateRequest(BaseUpdateRequest):
    """Partial update request for notification log row."""

    send_status: Optional[NotificationSendStatus] = Field(None, description="Current delivery status")
    provider_response: Optional[Dict[str, Any]] = Field(None, description="Provider response payload")
    error_message: Optional[str] = Field(None, description="Failure reason")
    retry_count: Optional[int] = Field(None, ge=0, description="Retries attempted")
    max_retry_attempts: Optional[int] = Field(None, ge=0, description="Maximum retries")
    retry_interval_minutes: Optional[int] = Field(None, ge=1, description="Retry delay in minutes")
    next_retry_at: Optional[datetime] = Field(None, description="Next retry timestamp")
    sent_at: Optional[datetime] = Field(None, description="Success timestamp")


class NotificationLogResponse(BaseResponse):
    """Response model for notification send log."""

    id: UUID = Field(..., description="Notification log ID")
    user_id: UUID = Field(..., description="Target user ID")
    notification_master_id: UUID = Field(..., description="Master template ID")
    notification_setting_id: Optional[UUID] = Field(None, description="Settings row used")
    channel: NotificationChannelCode = Field(..., description="Delivery channel")
    expo_push_token: Optional[str] = Field(None, description="Token used for send")
    payload_snapshot: Dict[str, Any] = Field(default_factory=dict, description="Resolved payload snapshot")
    send_status: NotificationSendStatus = Field(..., description="Current delivery status")
    provider_response: Optional[Dict[str, Any]] = Field(None, description="Raw provider response")
    error_message: Optional[str] = Field(None, description="Error details")
    retry_count: int = Field(..., description="Retries attempted")
    max_retry_attempts: int = Field(..., description="Maximum retries allowed")
    retry_interval_minutes: int = Field(..., description="Retry interval in minutes")
    next_retry_at: Optional[datetime] = Field(None, description="Next retry time")
    sent_at: Optional[datetime] = Field(None, description="Success timestamp")


class NotificationLogListResponse(ListResponse[NotificationLogResponse]):
    """Response model for notification logs list with pagination."""

    pass

