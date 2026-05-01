"""
Schemas for admin test push — send Expo notification to devices registered for a user.
"""

from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import BaseCreateRequest


class NotificationTestPushRequest(BaseCreateRequest):
    """Send a push to all push-enabled Expo tokens stored for ``user_id``."""

    model_config = ConfigDict(populate_by_name=True)

    user_id: UUID = Field(..., alias="userId", description="Target user UUID (must have rows in notification settings)")
    title: str = Field(
        default="Test notification",
        max_length=200,
        description="Push title shown on the device",
    )
    body: str = Field(
        default="Push test from the pharmacy API.",
        max_length=500,
        description="Push body text",
    )
    android_channel_id: Optional[str] = Field(
        default=None,
        alias="androidChannelId",
        max_length=120,
        description=(
            "Optional Expo ``channelId`` for Android deliveries; use ``delivery_default`` for the "
            "delivery partner APK or omit for default handling."
        ),
    )


class NotificationTestPushResultItem(BaseModel):
    """Per-token outcome aligned with Expo's ticket."""

    model_config = ConfigDict(populate_by_name=True)

    expo_push_token: str = Field(..., alias="expoPushToken")
    status: str = Field(..., description="Typically ``ok`` or ``error`` from Expo")
    detail: Optional[str] = Field(
        None,
        alias="detail",
        description="Error message when status is not ok",
    )


class NotificationTestPushResponse(BaseModel):
    """Aggregate result after calling Expo."""

    model_config = ConfigDict(populate_by_name=True)

    user_id: UUID = Field(..., alias="userId")
    tokens_targeted: int = Field(..., alias="tokensTargeted", description="Number of Expo messages built")
    results: List[NotificationTestPushResultItem] = Field(default_factory=list)
