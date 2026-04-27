"""
Notification Settings Schema
Pydantic models for user/device notification preference + token storage.

Recommended granularity:
- One row per user + device token (best for multi-device login support).
"""

from typing import Literal, Optional
from uuid import UUID

from pydantic import Field

from app.schemas.common import BaseCreateRequest, BaseResponse, BaseUpdateRequest, ListResponse

DevicePlatform = Literal["android", "ios", "web", "unknown"]


class NotificationSettingCreateRequest(BaseCreateRequest):
    """Create request for notification settings per user-device."""

    user_id: UUID = Field(..., description="Customer/User ID owning this device preference")
    device_id: Optional[str] = Field(None, max_length=255, description="App-generated device identifier")
    device_platform: DevicePlatform = Field("unknown", description="Client platform")
    expo_push_token: str = Field(..., max_length=255, description="Expo push token for this device")
    is_push_enabled: bool = Field(True, description="User preference for push notifications on this device")
    is_active: bool = Field(True, description="Whether this token row is active")

    model_config = {
        "json_schema_extra": {
            "example": {
                "user_id": "u123e456-7890-1234-5678-901234567890",
                "device_id": "a1f0f0dc-2fc8-4db7-a52f-61d6c1f54d20",
                "device_platform": "android",
                "expo_push_token": "ExponentPushToken[xxxxxxxxxxxxxxxxxxxxxx]",
                "is_push_enabled": True,
                "is_active": True,
            }
        }
    }


class NotificationSettingUpdateRequest(BaseUpdateRequest):
    """Partial update request for notification settings."""

    device_id: Optional[str] = Field(None, max_length=255, description="Device identifier")
    device_platform: Optional[DevicePlatform] = Field(None, description="Client platform")
    expo_push_token: Optional[str] = Field(None, max_length=255, description="Expo push token")
    is_push_enabled: Optional[bool] = Field(None, description="Push preference for this device")
    is_active: Optional[bool] = Field(None, description="Soft-enable/disable token row")


class NotificationSettingResponse(BaseResponse):
    """Response model for notification settings row."""

    id: UUID = Field(..., description="Notification settings ID")
    user_id: UUID = Field(..., description="Owner user ID")
    device_id: Optional[str] = Field(None, description="Device identifier")
    device_platform: DevicePlatform = Field(..., description="Client platform")
    expo_push_token: str = Field(..., description="Expo push token")
    is_push_enabled: bool = Field(..., description="Push enabled preference")
    is_active: bool = Field(..., description="Whether this row is active")


class NotificationSettingListResponse(ListResponse[NotificationSettingResponse]):
    """Response model for notification settings list with pagination."""

    pass

