"""
Per-user device push tokens (Expo) for notification delivery.
"""

from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.base_repository import BaseRepository
from app.db.models import NotificationSetting


class NotificationSettingsRepository(BaseRepository[NotificationSetting]):
    """Data access for ``M_notification_settings``."""

    def __init__(self, session: AsyncSession):
        super().__init__(NotificationSetting, session)

    async def get_by_user_id_and_expo_token(
        self, user_id: UUID, expo_push_token: str
    ) -> Optional[NotificationSetting]:
        """
        Lookup by unique (user_id, expo_push_token), including soft-deleted rows
        so a re-register can revive the row.
        """
        stmt = select(self.model).where(
            self.model.user_id == user_id,
            self.model.expo_push_token == expo_push_token,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_push_enabled_for_user(self, user_id: UUID) -> List[NotificationSetting]:
        """All active device rows with push enabled for ``user_id``."""
        stmt = (
            select(self.model)
            .where(
                self.model.user_id == user_id,
                self.model.is_deleted == False,  # noqa: E712
                self.model.is_active == True,  # noqa: E712
                self.model.is_push_enabled == True,  # noqa: E712
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_active_by_user_and_device_id(
        self, user_id: UUID, device_id: str
    ) -> List[NotificationSetting]:
        """Non-deleted rows for ``user_id`` with this ``device_id`` (same install, possibly multiple tokens)."""
        stmt = select(self.model).where(
            self.model.user_id == user_id,
            self.model.device_id == device_id,
            self.model.is_deleted == False,  # noqa: E712
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
