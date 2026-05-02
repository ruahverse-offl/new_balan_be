"""
Notification Settings Schema
Pydantic models for user/device notification preference + token storage.

Recommended granularity:
- One row per user + device token (best for multi-device login support).
"""

from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.schemas.common import BaseCreateRequest, BaseResponse, BaseUpdateRequest, ListResponse

DevicePlatform = Literal["android", "ios", "web", "unknown"]


class NotificationSettingCreateRequest(BaseCreateRequest):
    """Create request for notification settings per user-device."""

    user_id: UUID = Field(..., description="Customer/User ID owning this device preference")
    device_id: Optional[str] = Field(None, max_length=255, description="App-generated device identifier")
    device_platform: DevicePlatform = Field("unknown", description="Client platform")
    expo_push_token: str = Field(..., max_length=255, description="FCM registration token for this device")
    is_push_enabled: bool = Field(True, description="User preference for push notifications on this device")
    is_active: bool = Field(True, description="Whether this token row is active")

    model_config = {
        "json_schema_extra": {
            "example": {
                "user_id": "u123e456-7890-1234-5678-901234567890",
                "device_id": "a1f0f0dc-2fc8-4db7-a52f-61d6c1f54d20",
                "device_platform": "android",
                "expo_push_token": "fCM_token_example_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                "is_push_enabled": True,
                "is_active": True,
            }
        }
    }


class NotificationSettingUpdateRequest(BaseUpdateRequest):
    """Partial update request for notification settings."""

    device_id: Optional[str] = Field(None, max_length=255, description="Device identifier")
    device_platform: Optional[DevicePlatform] = Field(None, description="Client platform")
    expo_push_token: Optional[str] = Field(None, max_length=255, description="FCM registration token")
    is_push_enabled: Optional[bool] = Field(None, description="Push preference for this device")
    is_active: Optional[bool] = Field(None, description="Soft-enable/disable token row")


class NotificationSettingResponse(BaseResponse):
    """Response model for notification settings row."""

    id: UUID = Field(..., description="Notification settings ID")
    user_id: UUID = Field(..., description="Owner user ID")
    user_name: Optional[str] = Field(None, description="Owner user full name (enriched)")
    device_id: Optional[str] = Field(None, description="Device identifier")
    device_platform: str = Field(..., description="Client platform")
    expo_push_token: str = Field(..., description="FCM registration token")
    is_push_enabled: bool = Field(..., description="Push enabled preference")
    is_active: bool = Field(..., description="Whether this row is active")
    created_at: datetime = Field(..., description="When created")
    updated_at: datetime = Field(..., description="When last updated")


class NotificationSettingListResponse(ListResponse[NotificationSettingResponse]):
    """Response model for notification settings list with pagination."""

    pass


class MeNotificationSettingRegisterRequest(BaseCreateRequest):
    """
    Register or update this device's push token for the signed-in user.

    Upserts on (user_id, expo_push_token). ``user_id`` comes from JWT, not the body.
    For bare React Native, send the FCM device registration token in ``expo_push_token``.
    """

    expo_push_token: str = Field(
        ...,
        max_length=255,
        description="FCM registration token for this device.",
    )
    device_id: Optional[str] = Field(None, max_length=255, description="Optional stable app-generated device id")
    device_platform: DevicePlatform = Field("unknown", description="Client platform")
    is_push_enabled: bool = Field(True, description="Whether push is enabled for this device row")


class MeNotificationSettingRevokeRequest(BaseCreateRequest):
    """
    Soft-delete notification device rows for the signed-in user (call on logout).

    At least one of ``device_id`` or ``expo_push_token`` should be sent; both may be sent.
    """

    device_id: Optional[str] = Field(None, max_length=255, description="Installation / device id used at register time")
    expo_push_token: Optional[str] = Field(None, max_length=255, description="FCM token to revoke for this user")

    @model_validator(mode="after")
    def at_least_one_identifier(self) -> "MeNotificationSettingRevokeRequest":
        if not self.device_id and not self.expo_push_token:
            raise ValueError("Provide device_id and/or expo_push_token")
        return self


class MeNotificationSettingRevokeResponse(BaseModel):
    """Result of revoking notification device rows."""

    revoked_count: int = Field(..., ge=0, description="Number of rows soft-deleted")

