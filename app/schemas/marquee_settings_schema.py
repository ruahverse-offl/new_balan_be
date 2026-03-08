"""
Marquee Settings Schema
API models for coupon marquee visibility only (no delivery settings).
"""

from pydantic import BaseModel, Field


class MarqueeSettingsResponse(BaseModel):
    """Response for marquee visibility (read-only)."""
    show_marquee: bool = Field(..., description="Whether the coupon marquee is visible on the site")


class MarqueeSettingsUpdate(BaseModel):
    """Request to update only marquee visibility."""
    show_marquee: bool = Field(..., description="True = visible, False = hidden")
