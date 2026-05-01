"""
Schemas for the signed-in user's notification inbox (mobile / delivery app).
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class MyNotificationItem(BaseModel):
    """One row in the user's notification list (derived from ``T_notification_logs``)."""

    id: UUID = Field(..., description="Notification log ID")
    title: str = Field(..., description="Short title from payload snapshot")
    body: Optional[str] = Field(None, description="Body text from payload snapshot")
    send_status: str = Field(..., description="Delivery status (queued, sent, failed, …)")
    channel: str = Field(..., description="Channel (push, sms, …)")
    created_at: datetime = Field(..., description="When the log row was created")
    sent_at: Optional[datetime] = Field(None, description="When the provider reported success")


class MyNotificationsResponse(BaseModel):
    """Up to 30 most recent notifications for the current user."""

    items: List[MyNotificationItem] = Field(default_factory=list)
